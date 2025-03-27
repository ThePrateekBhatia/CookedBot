import sys
import logging
import os
from importlib import import_module
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from subprocess import run

# Configure logging
log_file = "log.txt"
rlog_file = "rlog.txt"

for file in [log_file, rlog_file]:
    if os.path.exists(file):
        os.remove(file)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logging.getLogger("pymongo").setLevel(logging.ERROR)

# Load config
try:
    settings = import_module("config")
    config_file = {
        key: value.strip() if isinstance(value, str) else value
        for key, value in vars(settings).items()
        if not key.startswith("__")
    }
except ModuleNotFoundError as e:
    logger.error("Config module not found: %s", e)
    sys.exit(1)

BOT_TOKEN = config_file.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN variable is missing! Exiting now")
    sys.exit(1)

BOT_ID = BOT_TOKEN.split(":", 1)[0]

# Fetch data from MongoDB
DATABASE_URL = config_file.get("DATABASE_URL", "").strip()
if DATABASE_URL:
    try:
        client = MongoClient(DATABASE_URL, server_api=ServerApi("1"))
        db = client.mltb

        old_config = db.settings.deployConfig.find_one({"_id": BOT_ID}, {"_id": 0})
        config_dict = db.settings.config.find_one({"_id": BOT_ID})

        if config_dict and (not old_config or old_config == config_file):
            config_file.update({
                "UPSTREAM_REPO": config_dict.get("UPSTREAM_REPO", ""),
                "UPSTREAM_BRANCH": config_dict.get("UPSTREAM_BRANCH", "master"),
            })

        client.close()
    except Exception as e:
        logger.error("Database ERROR: %s", e)

# Git update
UPSTREAM_REPO = config_file.get("UPSTREAM_REPO", "").strip()
UPSTREAM_BRANCH = config_file.get("UPSTREAM_BRANCH", "master").strip()

if UPSTREAM_REPO:
    if os.path.exists(".git"):
        run(["rm", "-rf", ".git"], check=True)

    git_commands = [
        "git init -q",
        "git config --global user.email bhatiaprateek111@gmail.com",
        "git config --global user.name 'Prateek Bhatia'",
        "git add .",
        "git commit -sm 'update' -q",
        f"git remote add origin {UPSTREAM_REPO}",
        "git fetch origin -q",
        f"git reset --hard origin/{UPSTREAM_BRANCH} -q",
    ]

    result = run(" && ".join(git_commands), shell=True)

    if result.returncode == 0:
        logger.info("Successfully updated with latest commit from UPSTREAM_REPO")
    else:
        logger.error("Error updating from UPSTREAM_REPO. Check if it's valid.")
