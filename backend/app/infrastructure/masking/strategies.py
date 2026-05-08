import hashlib
import string
import random
from typing import Any
from datetime import datetime, timedelta
from faker import Faker

from app.domain.interfaces.masking_strategy import MaskingStrategy


class SubstitutionStrategy(MaskingStrategy):
    def mask(self, value: Any, **options) -> Any:
        if value is None:
            return None
        provider = options.get("provider", "name")
        seed_value = f"{provider}:{value}"
        numeric_seed = int(hashlib.sha256(seed_value.encode("utf-8")).hexdigest(), 16) % (2**32)
        faker = Faker()
        faker.seed_instance(numeric_seed)
        try:
            fake_func = getattr(faker, provider)
            return fake_func()
        except AttributeError:
            return faker.word()


class HashingStrategy(MaskingStrategy):
    def mask(self, value: Any, **options) -> Any:
        if value is None:
            return None
        salt = options.get("salt", "")
        payload = f"{value}{salt}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


class RedactionStrategy(MaskingStrategy):
    def mask(self, value: Any, **options) -> Any:
        if value is None:
            return None
        mask_char = options.get("mask_char", "*")
        return mask_char * len(str(value))


class NullificationStrategy(MaskingStrategy):
    def mask(self, value: Any, **options) -> Any:
        return None

class FPEStrategy(MaskingStrategy):
    def mask(self, value: Any, **options) -> Any:
        if value is None:
            return None
        
        val_str = str(value)
        seed_str = options.get("seed", "default")
        seed_val = int(hashlib.sha256(f"{seed_str}:{val_str}".encode("utf-8")).hexdigest(), 16) % (2**32)
        rng = random.Random(seed_val)
        
        result = []
        for char in val_str:
            if char.isdigit():
                result.append(str(rng.randint(0, 9)))
            elif char.isalpha():
                if char.isupper():
                    result.append(rng.choice(string.ascii_uppercase))
                else:
                    result.append(rng.choice(string.ascii_lowercase))
            else:
                result.append(char)
        return "".join(result)

class PerturbationStrategy(MaskingStrategy):
    def mask(self, value: Any, **options) -> Any:
        if value is None:
            return None
            
        variance_type = options.get("variance_type", "percentage") # 'percentage' or 'days'
        try:
            variance_value = float(options.get("variance_value", 10))
        except (ValueError, TypeError):
            variance_value = 10.0
            
        seed_val = int(hashlib.sha256(str(value).encode("utf-8")).hexdigest(), 16) % (2**32)
        rng = random.Random(seed_val)
        factor = rng.uniform(-variance_value, variance_value)
        
        if variance_type == "percentage":
            try:
                num = float(value)
                perturbed = num * (1 + factor / 100.0)
                if isinstance(value, int) or str(value).isdigit():
                    return int(perturbed)
                # Keep float formatting simple
                return round(perturbed, 4)
            except ValueError:
                return value
                
        elif variance_type == "days":
            try:
                dt = None
                if isinstance(value, datetime):
                    dt = value
                else:
                    val_s = str(value).replace('Z', '+00:00')
                    try:
                        dt = datetime.fromisoformat(val_s)
                    except ValueError:
                        dt = datetime.strptime(val_s[:10], "%Y-%m-%d")
                        
                perturbed_dt = dt + timedelta(days=factor)
                
                if isinstance(value, str):
                    if "T" in str(value):
                        return perturbed_dt.isoformat()
                    return perturbed_dt.strftime("%Y-%m-%d")
                return perturbed_dt
            except (ValueError, TypeError):
                return value
                
        return value
