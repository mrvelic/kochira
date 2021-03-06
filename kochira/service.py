import functools
import re
import logging

logger = logging.getLogger(__name__)


class Service:
    """
    A service provides the bot with additional facilities.
    """
    SERVICES_PACKAGE = 'kochira.services'

    EAT = object()

    def __init__(self, name, commands=None, tasks=None):
        self.name = name
        self.hooks = {}
        self.tasks = []
        self.on_setup = None
        self.on_shutdown = None
        self.logger = logging.getLogger(self.name)

    def hook(self, hook):
        """
        Register a hook with the service.
        """

        def _decorator(f):
            self.hooks.setdefault(hook, []).append(f)
            return f

        return _decorator

    def command(self, pattern, mention=False, strip=True, re_flags=re.I,
                eat=True):
        """
        Register a command for use with the bot.

        ``mention`` specifies that the bot's nickname must be mentioned.
        """

        pat = re.compile(pattern, re_flags)

        def _decorator(f):
            @functools.wraps(f)
            def _command_handler(client, origin, target, message):
                if strip:
                    message = message.strip()

                if mention:
                    first, _, rest = message.partition(" ")
                    first = first.rstrip(",:")

                    if first != client.nickname:
                        return

                    message = rest

                match = pat.match(message)
                if match is None:
                    return

                kwargs = match.groupdict()

                for k, v in kwargs.items():
                    if k in f.__annotations__ and v is not None:
                        kwargs[k] = f.__annotations__[k](v)

                r = f(client, origin, target, **kwargs)

                if r is not None:
                    return r

                if eat:
                    return Service.EAT

            self.hook("message")(_command_handler)
            return f

        return _decorator

    def task(self, f):
        """
        Register a new task. If the task is designed to be used as a timer,
        interval should be `None`.
        """

        f.service = self
        self.tasks.append(f)
        return f

    def setup(self, f):
        """
        Register a setup function.
        """
        self.on_setup = f

    def shutdown(self, f):
        """
        Register a shutdown function.
        """
        self.on_shutdown = f

    def run_hooks(self, hook, client, *args):
        """
        Attempt to dispatch a command to all command handlers.
        """

        for hook in self.hooks.get(hook, []):
            try:
                r = hook(client, *args)
                if r is Service.EAT:
                    return Service.EAT
            except BaseException:
                self.logger.error("Hook processing failed", exc_info=True)

    def run_setup(self, bot):
        """
        Run all setup functions for the service.
        """
        if self.on_setup is not None:
            self.on_setup(bot)

    def run_shutdown(self, bot):
        """
        Run all setup functions for the service.
        """
        if self.on_shutdown is not None:
            self.on_shutdown(bot)

    def config_for(self, bot):
        """
        Get the configuration dictionary.
        """
        return bot.config["services"][self.name]

    def storage_for(self, bot):
        """
        Get the disposable storage object.
        """
        _, storage = bot.services[self.name]
        return storage


def background(f):
    """
    Defer a command to run in the background.
    """

    @functools.wraps(f)
    def _inner(client, *args, **kwargs):
        future = client.bot.executor.submit(f, client, *args, **kwargs)

        @future.add_done_callback
        def on_complete(future):
            exc = future.exception()
            if exc is not None:
                logger.error("Command error", exc_info=exc)

    return _inner
