"""
Gestion sécurisée des mots de passe pour Swanky Apartments PMS.

Les mots de passe ne sont jamais stockés en clair : on stocke uniquement un hash
(PBKDF2-HMAC-SHA256, 200 000 itérations) accompagné d'un sel (salt) unique par
utilisateur. PBKDF2 fait partie de la bibliothèque standard de Python (module
hashlib) — aucune dépendance externe n'est nécessaire.
"""

import hashlib
import secrets
from typing import Optional, Tuple

ITERATIONS = 200_000


def hash_password(password: str, salt_hex: Optional[str] = None) -> Tuple[str, str]:
    """
    Calcule le hash d'un mot de passe. Si aucun sel n'est fourni, un nouveau
    sel aléatoire est généré (cas de la création de compte).
    Retourne (hash_hex, salt_hex).
    """
    if salt_hex is None:
        salt_hex = secrets.token_hex(16)
    salt_bytes = bytes.fromhex(salt_hex)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, ITERATIONS)
    return pwd_hash.hex(), salt_hex


def verify_password(password: str, salt_hex: str, stored_hash_hex: str) -> bool:
    """Vérifie un mot de passe fourni contre le hash stocké, en temps constant."""
    computed_hash, _ = hash_password(password, salt_hex)
    return secrets.compare_digest(computed_hash, stored_hash_hex)
