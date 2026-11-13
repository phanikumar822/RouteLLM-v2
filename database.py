import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("RouteLLM.Database")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "routellm")

_client = None
_db = None
_is_connected = False

def init_db():
    global _client, _db, _is_connected
    if not MONGODB_URI:
        logger.info("[Database] No MONGODB_URI configured. Using local JSON / text fallback.")
        _is_connected = False
        return False

    try:
        from pymongo import MongoClient
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
        # Verify connection by pinging admin
        _client.admin.command("ping")
        _db = _client[MONGODB_DB_NAME]
        _is_connected = True
        logger.info(f"[Database] Connected to MongoDB: {MONGODB_DB_NAME}")
        
        # Ensure indexes
        _db.users.create_index("username", unique=True)
        _db.chat_history.create_index("timestamp")

        # Migrate local files if collections are empty
        _migrate_local_data()
        return True
    except Exception as e:
        logger.warning(f"[Database] MongoDB connection failed ({e}). Operating in local file mode (users.json / history.txt).")
        _is_connected = False
        return False

def _migrate_local_data():
    """Migrate data from users.json and history.txt to MongoDB if DB is fresh."""
    global _db
    if not _is_connected or _db is None:
        return

    # Migrate users
    try:
        if os.path.exists("users.json") and _db.users.count_documents({}) == 0:
            with open("users.json", "r", encoding="utf-8") as f:
                users_data = json.load(f)
            docs = []
            for uname, phash in users_data.items():
                docs.append({
                    "username": uname,
                    "password_hash": phash,
                    "created_at": datetime.utcnow()
                })
            if docs:
                _db.users.insert_many(docs)
                logger.info(f"[Database] Migrated {len(docs)} users from users.json to MongoDB.")
    except Exception as e:
        logger.error(f"[Database] Error migrating users: {e}")

    # Migrate history
    try:
        if os.path.exists("history.txt") and _db.chat_history.count_documents({}) == 0:
            with open("history.txt", "r", encoding="utf-8") as f:
                content = f.read()
            parts = [p.strip() for p in content.split("=" * 70) if p.strip()]
            docs = []
            for part in parts:
                lines = part.split("\n")
                model = "UNKNOWN"
                query = ""
                answer_lines = []
                mode = "header"
                for line in lines:
                    if line.startswith("MODEL:"):
                        model = line.replace("MODEL:", "").strip()
                    elif line.startswith("QUERY:"):
                        query = line.replace("QUERY:", "").strip()
                    elif line.startswith("RESPONSE:"):
                        mode = "response"
                    elif mode == "response":
                        answer_lines.append(line)
                answer = "\n".join(answer_lines).strip()
                if query or answer:
                    docs.append({
                        "model": model,
                        "query": query,
                        "answer": answer,
                        "timestamp": datetime.utcnow()
                    })
            if docs:
                _db.chat_history.insert_many(docs)
                logger.info(f"[Database] Migrated {len(docs)} chat entries from history.txt to MongoDB.")
    except Exception as e:
        logger.error(f"[Database] Error migrating history: {e}")

# --- User Management ---

def load_users():
    """Returns a dict {username: password_hash}."""
    global _db, _is_connected
    if _is_connected and _db is not None:
        try:
            users_cursor = _db.users.find({})
            return {u["username"]: u["password_hash"] for u in users_cursor}
        except Exception as e:
            logger.error(f"[Database] Error reading users from MongoDB: {e}")

    # Fallback to local users.json
    if not os.path.exists("users.json"):
        return {}
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_user(username, password_hash):
    """Saves a user to MongoDB and updates users.json for sync/fallback."""
    global _db, _is_connected
    success = False

    if _is_connected and _db is not None:
        try:
            _db.users.update_one(
                {"username": username},
                {"$set": {"password_hash": password_hash, "updated_at": datetime.utcnow()}},
                upsert=True
            )
            success = True
        except Exception as e:
            logger.error(f"[Database] Error saving user to MongoDB: {e}")

    # Always keep local file updated as fallback
    try:
        users = {}
        if os.path.exists("users.json"):
            with open("users.json", "r", encoding="utf-8") as f:
                users = json.load(f)
        users[username] = password_hash
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
        success = True
    except Exception as e:
        logger.error(f"[Database] Error updating users.json: {e}")

    return success

# --- Chat History Management ---

def load_history():
    """Loads recent history (last 10 entries up to 12000 chars) for prompt routing context."""
    global _db, _is_connected
    if _is_connected and _db is not None:
        try:
            cursor = _db.chat_history.find().sort("timestamp", -1).limit(10)
            records = list(cursor)
            records.reverse()  # Chronological order
            parts = []
            for r in records:
                part = f"MODEL: {r.get('model', 'UNKNOWN')}\nQUERY: {r.get('query', '')}\nRESPONSE:\n{r.get('answer', '')}"
                parts.append(part)
            recent_history = ("\n\n" + "=" * 70 + "\n").join(parts)
            if recent_history:
                recent_history = "=" * 70 + "\n" + recent_history + "\n" + "=" * 70
            if len(recent_history) > 12000:
                recent_history = recent_history[-12000:]
            return recent_history
        except Exception as e:
            logger.error(f"[Database] Error loading history from MongoDB: {e}")

    # Fallback to history.txt
    if not os.path.exists("history.txt"):
        return ""
    try:
        with open("history.txt", "r", encoding="utf-8") as file:
            history = file.read()
        parts = history.split("=" * 70)
        parts = [part.strip() for part in parts if part.strip()]
        recent_parts = parts[-10:]
        recent_history = "\n\n".join(recent_parts)
        if len(recent_history) > 12000:
            recent_history = recent_history[-12000:]
        return recent_history
    except Exception:
        return ""

def save_history(model, query, answer):
    """Saves a conversation turn to MongoDB and history.txt."""
    global _db, _is_connected
    if _is_connected and _db is not None:
        try:
            _db.chat_history.insert_one({
                "model": model,
                "query": query,
                "answer": answer,
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            logger.error(f"[Database] Error inserting history into MongoDB: {e}")

    # Always append to history.txt as local backup
    try:
        with open("history.txt", "a", encoding="utf-8") as file:
            file.write("\n" + "=" * 70 + "\n")
            file.write(f"MODEL: {model}\n")
            file.write(f"QUERY: {query}\n")
            file.write("RESPONSE:\n")
            file.write(answer)
            file.write("\n" + "=" * 70 + "\n")
    except Exception as e:
        logger.error(f"[Database] Error writing to history.txt: {e}")

def get_history_text():
    """Returns the full history text for the UI modal."""
    global _db, _is_connected
    if _is_connected and _db is not None:
        try:
            cursor = _db.chat_history.find().sort("timestamp", 1)
            parts = []
            for r in cursor:
                part = f"MODEL: {r.get('model', 'UNKNOWN')}\nQUERY: {r.get('query', '')}\nRESPONSE:\n{r.get('answer', '')}"
                parts.append(part)
            if parts:
                return "\n\n" + ("=" * 70 + "\n\n").join(parts) + "\n\n" + ("=" * 70)
            return "No history found."
        except Exception as e:
            logger.error(f"[Database] Error fetching history text: {e}")

    # Fallback
    if not os.path.exists("history.txt"):
        return "No history found."
    try:
        with open("history.txt", "r", encoding="utf-8") as f:
            content = f.read()
        return content if content.strip() else "No history found."
    except Exception:
        return "No history found."

def clear_history():
    """Clears history in MongoDB and removes history.txt."""
    global _db, _is_connected
    if _is_connected and _db is not None:
        try:
            _db.chat_history.delete_many({})
        except Exception as e:
            logger.error(f"[Database] Error clearing history in MongoDB: {e}")

    if os.path.exists("history.txt"):
        try:
            os.remove("history.txt")
        except Exception:
            pass

def get_db_status():
    return {
        "connected": _is_connected,
        "database_type": "mongodb" if _is_connected else "local_fallback",
        "uri": MONGODB_URI if _is_connected else None,
        "database_name": MONGODB_DB_NAME if _is_connected else None
    }
