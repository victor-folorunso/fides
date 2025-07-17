from tortoise import fields
from tortoise.models import Model

class AirdropClaim(Model):
    id = fields.IntField(pk=True)
    wallet_address = fields.CharField(max_length=255, unique=True)
    claimed = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "airdrop_claim"

class VaultRequest(Model):
    id = fields.IntField(pk=True)
    wallet_address = fields.CharField(max_length=255)
    amount = fields.DecimalField(max_digits=20, decimal_places=8)
    duration = fields.IntField()  # in months
    claimed = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "vault_request"
 
class VaultStake(Model):
    id = fields.IntField(pk=True)
    wallet_address = fields.CharField(max_length=255)
    amount = fields.DecimalField(max_digits=20, decimal_places=8)
    duration = fields.IntField()  # in months
    tx_hash = fields.CharField(max_length=255)
    matured_on = fields.IntField()  # Unix timestamp
    claimed = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "vault_stake"
