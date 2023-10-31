# import logging
# import logging.config
# import sys

# _SYSLOG_PLATFORM_ADDRESS = {
#     "win32": ("localhost", 514),
#     "darwin": "/var/run/syslog",
# }

# logging.basicConfig(
#     format=(
#         "[zyg] %(levelname)s %(asctime)s %(module)s %(process)d "
#         "%(filename)s:%(lineno)d %(message)s"
#     ),
#     datefmt="%Y-%m-%d %H:%M:%S %Z",
#     level=logging.INFO,
# )


# logging.config.dictConfig(
#     {
#         "version": 1,
#         "formatters": {
#             "default": {
#                 "format": (
#                     "[zyg]|%(levelname)s|%(asctime)s|%(process)d|%(module)s|"
#                     "%(filename)s:%(lineno)d|%(funcName)s|"
#                     "%(message)s"
#                 ),
#                 "datefmt": "%Y-%m-%d %H:%M:%S %Z",
#             },
#         },
#         "handlers": {
#             "console": {
#                 "level": "INFO",
#                 "class": "logging.StreamHandler",
#                 "formatter": "default",
#                 "stream": "ext://sys.stdout",
#             },
#             "syslog": {
#                 "level": "INFO",
#                 "class": "logging.handlers.SysLogHandler",
#                 "formatter": "default",
#                 "address": _SYSLOG_PLATFORM_ADDRESS.get(sys.platform, "/dev/log"),
#             },
#         },
#         "root": {
#             "handlers": ["console", "syslog"],
#             "level": "INFO",
#         },
#         "loggers": {
#             "uvicorn": {
#                 "handlers": ["console", "syslog"],
#                 "level": "INFO",
#                 "propagate": False,
#             },
#         },
#     }
# )

# logger = logging.getLogger(__name__)
