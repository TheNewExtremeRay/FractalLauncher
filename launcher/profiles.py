"""
Profile Manager — handles multiple accounts and game profiles.
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional


PROFILES_FILE = os.path.join(os.path.expanduser("~"), ".FractalLauncher", "profiles.json")


@dataclass
class Account:
    id: str
    username: str
    auth_type: str           # "microsoft" or "offline"
    uuid: str                # MC UUID (real or fake)
    access_token: str        # MC access token or "offline"
    refresh_token: str = ""  # MS refresh token
    skin_url: str = ""       # Skin URL (Microsoft accounts)
    skin_path: str = ""      # Local .png skin file (offline mode)
    skin_model: str = "default"  # "default" (Steve) or "slim" (Alex)
    cape_path:  str = ""      # Local .png cape file (offline mode)


@dataclass
class Profile:
    id: str
    name: str
    version: str
    mod_loader: str
    mod_loader_version: str
    account_id: str
    ram_mb: int
    jvm_args: str
    game_dir: str
    resolution_w: int = 854
    resolution_h: int = 480
    fullscreen: bool = False


class ProfileManager:
    def __init__(self):
        self.accounts: list[Account] = []
        self.profiles: list[Profile] = []
        self.active_account_id: Optional[str] = None
        self.active_profile_id: Optional[str] = None
        self._ensure_dir()
        self.load()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(PROFILES_FILE), exist_ok=True)

    def save(self):
        data = {
            "accounts": [asdict(a) for a in self.accounts],
            "profiles": [asdict(p) for p in self.profiles],
            "active_account_id": self.active_account_id,
            "active_profile_id": self.active_profile_id,
        }
        tmp = PROFILES_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, PROFILES_FILE)

    def load(self):
        if not os.path.exists(PROFILES_FILE):
            return
        try:
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ProfileManager] Failed to parse profiles.json: {e}")
            return
        # Only pass known fields so old JSON missing new fields doesn't crash
        acc_fields  = set(Account.__dataclass_fields__.keys())
        prof_fields = set(Profile.__dataclass_fields__.keys())
        self.accounts = []
        for a in data.get("accounts", []):
            try:
                self.accounts.append(Account(**{k: v for k, v in a.items() if k in acc_fields}))
            except Exception as e:
                print(f"[ProfileManager] Skipping corrupt account entry: {e}")
        self.profiles = []
        for p in data.get("profiles", []):
            try:
                self.profiles.append(Profile(**{k: v for k, v in p.items() if k in prof_fields}))
            except Exception as e:
                print(f"[ProfileManager] Skipping corrupt profile entry: {e}")
        self.active_account_id = data.get("active_account_id")
        self.active_profile_id = data.get("active_profile_id")

    # ── Accounts ─────────────────────────────────────────────────────────────

    def add_offline_account(self, username: str) -> Account:
        fake_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, username))
        acc = Account(
            id=str(uuid.uuid4()),
            username=username,
            auth_type="offline",
            uuid=fake_uuid,
            access_token="offline",
        )
        self.accounts.append(acc)
        if self.active_account_id is None:
            self.active_account_id = acc.id
        self.save()
        return acc

    def add_microsoft_account(self, username: str, mc_uuid: str,
                               access_token: str, refresh_token: str,
                               skin_url: str = "") -> Account:
        acc = Account(
            id=str(uuid.uuid4()),
            username=username,
            auth_type="microsoft",
            uuid=mc_uuid,
            access_token=access_token,
            refresh_token=refresh_token,
            skin_url=skin_url,
        )
        self.accounts.append(acc)
        if self.active_account_id is None:
            self.active_account_id = acc.id
        self.save()
        return acc

    def update_account_tokens(self, account_id: str, access_token: str, refresh_token: str):
        acc = self.get_account(account_id)
        if acc:
            acc.access_token = access_token
            acc.refresh_token = refresh_token
            self.save()

    def remove_account(self, account_id: str):
        self.accounts = [a for a in self.accounts if a.id != account_id]
        if self.active_account_id == account_id:
            self.active_account_id = self.accounts[0].id if self.accounts else None
        self.profiles = [p for p in self.profiles if p.account_id != account_id]
        self.save()

    def get_account(self, account_id: str) -> Optional[Account]:
        return next((a for a in self.accounts if a.id == account_id), None)

    @property
    def active_account(self) -> Optional[Account]:
        return self.get_account(self.active_account_id) if self.active_account_id else None

    # ── Profiles ─────────────────────────────────────────────────────────────

    def add_profile(self, name: str, version: str, mod_loader: str = "vanilla",
                    mod_loader_version: str = "latest", account_id: str = None,
                    ram_mb: int = 4096, jvm_args: str = "",
                    game_dir: str = "", profile_id: str = None) -> Profile:
        if account_id is None:
            account_id = self.active_account_id or ""
        profile = Profile(
            id=profile_id or str(uuid.uuid4()),
            name=name,
            version=version,
            mod_loader=mod_loader,
            mod_loader_version=mod_loader_version,
            account_id=account_id,
            ram_mb=ram_mb,
            jvm_args=jvm_args,
            game_dir=game_dir,
        )
        self.profiles.append(profile)
        if self.active_profile_id is None:
            self.active_profile_id = profile.id
        self.save()
        return profile

    def update_profile(self, profile_id: str, **kwargs):
        p = self.get_profile(profile_id)
        if p:
            for k, v in kwargs.items():
                if hasattr(p, k):
                    setattr(p, k, v)
            self.save()

    def remove_profile(self, profile_id: str):
        self.profiles = [p for p in self.profiles if p.id != profile_id]
        if self.active_profile_id == profile_id:
            self.active_profile_id = self.profiles[0].id if self.profiles else None
        self.save()

    def get_profile(self, profile_id: str) -> Optional[Profile]:
        return next((p for p in self.profiles if p.id == profile_id), None)

    @property
    def active_profile(self) -> Optional[Profile]:
        return self.get_profile(self.active_profile_id) if self.active_profile_id else None
