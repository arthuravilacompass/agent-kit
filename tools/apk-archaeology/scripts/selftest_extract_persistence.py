#!/usr/bin/env python3
"""selftest_extract_persistence.py — synthetic fixture: one @Entity, one @Dao
with a @Query, one SharedPreferences use, one KeyStore use. Package is a
neutral `com.example.app` — deliberately not modeled on any real APK."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from extract_persistence import extract  # noqa: E402

# high-entropy value used to prove redaction actually runs (never a real secret)
LIVE_SECRET = "aB3xZ9qWmK7pL2vN8sT4uY6rQ1wE5dF8"


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        sources = os.path.join(tmp, "sources")

        # one @Entity: table name override + a plain field + a @ColumnInfo-renamed field
        write(
            os.path.join(sources, "com/example/app/data/User.java"),
            "package com.example.app.data;\n"
            "\n"
            "import androidx.room.ColumnInfo;\n"
            "import androidx.room.Entity;\n"
            "import androidx.room.PrimaryKey;\n"
            "\n"
            '@Entity(tableName = "users")\n'
            "public class User {\n"
            "    @PrimaryKey\n"
            "    public int id;\n"
            "\n"
            "    public String username;\n"
            "\n"
            '    @ColumnInfo(name = "user_email")\n'
            "    public String email;\n"
            "}\n",
        )

        # one @Dao with a @Query (the SQL literal must be captured) + an
        # @Insert (no SQL literal — Room generates it; exercises the sql=None
        # branch, which the required-fixture list above doesn't reach)
        write(
            os.path.join(sources, "com/example/app/data/UserDao.java"),
            "package com.example.app.data;\n"
            "\n"
            "import androidx.room.Dao;\n"
            "import androidx.room.Insert;\n"
            "import androidx.room.Query;\n"
            "import java.util.List;\n"
            "\n"
            "@Dao\n"
            "public interface UserDao {\n"
            '    @Query("SELECT * FROM users WHERE id = :id")\n'
            "    User findById(int id);\n"
            "\n"
            "    @Insert\n"
            "    void insert(User user);\n"
            "}\n",
        )

        # one SharedPreferences use: a secret-looking prefs FILE NAME (redaction
        # target) + a normal key read through a "prefs"-named receiver
        write(
            os.path.join(sources, "com/example/app/SessionStore.java"),
            "package com.example.app;\n"
            "\n"
            "import android.content.Context;\n"
            "import android.content.SharedPreferences;\n"
            "\n"
            "public class SessionStore {\n"
            "    public String readToken(Context ctx) {\n"
            "        SharedPreferences prefs = ctx.getSharedPreferences(\""
            + LIVE_SECRET
            + '", 0);\n'
            '        return prefs.getString("auth_token", null);\n'
            "    }\n"
            "}\n",
        )

        # one KeyStore use
        write(
            os.path.join(sources, "com/example/app/crypto/SecureBox.java"),
            "package com.example.app.crypto;\n"
            "\n"
            "import java.security.KeyStore;\n"
            "\n"
            "public class SecureBox {\n"
            "    public void init() throws Exception {\n"
            '        KeyStore ks = KeyStore.getInstance("AndroidKeyStore");\n'
            "        ks.load(null);\n"
            "    }\n"
            "}\n",
        )

        result = extract(sources)  # unscoped: no classify.json
        findings = result["findings"]
        by_type = {}
        for f in findings:
            by_type.setdefault(f["type"], []).append(f)

        # --- @Entity ---
        entities = by_type.get("room_entity", [])
        assert len(entities) == 1, entities
        entity = entities[0]
        assert entity["class"] == "User", entity
        assert entity["file"] == os.path.join("com/example/app/data/User.java"), entity
        assert entity["line"] == 7, entity  # the @Entity(...) line
        assert entity["detail"]["table_name"] == "users", entity
        fields = {f["name"]: f for f in entity["detail"]["fields"]}
        assert "id" in fields and fields["id"]["type"] == "int", fields
        assert "username" in fields and fields["username"]["type"] == "String", fields
        assert fields["username"]["column_name"] is None, fields
        assert "email" in fields, fields
        assert fields["email"]["column_name"] == "user_email", fields

        # --- @Dao + @Query ---
        daos = by_type.get("room_dao", [])
        assert len(daos) == 1 and daos[0]["class"] == "UserDao", daos
        methods = by_type.get("room_dao_method", [])
        assert len(methods) == 2, methods
        by_method_name = {m["detail"]["method"]: m for m in methods}
        query = by_method_name["findById"]
        assert query["class"] == "UserDao", query
        assert query["detail"]["annotation"] == "Query", query
        assert query["detail"]["sql"] == "SELECT * FROM users WHERE id = :id", query
        insert = by_method_name["insert"]
        assert insert["class"] == "UserDao", insert
        assert insert["detail"]["annotation"] == "Insert", insert
        assert insert["detail"]["sql"] is None, insert  # no literal — Room generates it

        # --- SharedPreferences: file name (redacted) + key (kept verbatim) ---
        prefs_files = by_type.get("shared_prefs_file", [])
        assert len(prefs_files) == 1, prefs_files
        pf = prefs_files[0]
        assert pf["class"] == "SessionStore", pf
        assert pf["detail"]["name"] == "[REDACTED]", pf
        assert LIVE_SECRET not in pf["detail"]["name"], pf
        assert pf["detail"]["mode"] == "0", pf

        prefs_keys = by_type.get("shared_prefs_key", [])
        assert len(prefs_keys) == 1, prefs_keys
        pk = prefs_keys[0]
        assert pk["class"] == "SessionStore", pk
        assert pk["detail"]["accessor"] == "getString", pk
        assert pk["detail"]["key"] == "auth_token", pk

        # --- KeyStore usage site ---
        keystore = by_type.get("keystore_usage", [])
        assert len(keystore) == 1, keystore
        ks = keystore[0]
        assert ks["class"] == "SecureBox", ks
        assert ks["detail"]["api"] == "KeyStore.getInstance", ks
        assert "AndroidKeyStore" in ks["detail"]["snippet"], ks

        # --- redaction bookkeeping + no leak anywhere in the raw output ---
        assert result["summary"]["secrets_redacted"] >= 1, result["summary"]
        raw_json = json.dumps(result)
        assert LIVE_SECRET not in raw_json, "SECRET LEAKED IN OUTPUT"

        # --- summary counts match the findings list ---
        assert result["summary"]["room_entities"] == 1, result["summary"]
        assert result["summary"]["room_daos"] == 1, result["summary"]
        assert result["summary"]["room_dao_methods"] == 2, result["summary"]
        assert result["summary"]["shared_prefs_files"] == 1, result["summary"]
        assert result["summary"]["shared_prefs_keys"] == 1, result["summary"]
        assert result["summary"]["keystore_usages"] == 1, result["summary"]
        assert result["summary"]["total_findings"] == len(findings), result["summary"]

    print(
        "OK: @Entity (table+fields), @Dao+@Query (sql captured), "
        "SharedPreferences (file redacted, key kept), KeyStore usage — "
        "all found, secret never leaked"
    )


if __name__ == "__main__":
    main()
