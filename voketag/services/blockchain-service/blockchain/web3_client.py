"""
Web3 client for blockchain integration
"""

from typing import Dict, Optional
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
import time

from blockchain_service.config.settings import settings
from blockchain_service.core.logging_config import get_logger

logger = get_logger(__name__)

# Web3 client singleton
_web3_client: Optional[Web3] = None


def get_web3_client() -> Web3:
    """
    Get or create Web3 client.
    
    Returns:
        Web3 instance connected to blockchain network
    """
    global _web3_client
    
    if _web3_client is None:
        _web3_client = _create_web3_client()
    
    # Test connection
    if not _web3_client.is_connected():
        logger.warning("Web3 not connected, reconnecting...")
        _web3_client = _create_web3_client()
    
    return _web3_client


def _create_web3_client() -> Web3:
    """
    Create Web3 client.
    
    Returns:
        Web3 instance
    """
    if not settings.blockchain_rpc_url:
        # Mock mode for development
        logger.warning("Blockchain RPC URL not configured, using mock mode")
        return _create_mock_web3()
    
    w3 = Web3(Web3.HTTPProvider(settings.blockchain_rpc_url))
    
    # Add PoA middleware for networks like Polygon
    if settings.blockchain_network in ["polygon", "bsc"]:
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    # Test connection
    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to blockchain: {settings.blockchain_rpc_url}")
    
    logger.info(f"Connected to blockchain: {settings.blockchain_network}")
    logger.info(f"Current block: {w3.eth.block_number}")
    
    return w3


def _create_mock_web3() -> Web3:
    """Create mock Web3 for development without real blockchain."""
    logger.warning("Creating MOCK Web3 client (not connected to real blockchain)")
    
    # Mock Web3 that returns fake data
    class MockWeb3:
        def __init__(self):
            self.eth = MockEth()
        
        def is_connected(self):
            return True
        
        def to_wei(self, amount, unit):
            return amount * (10 ** 18 if unit == 'ether' else 10 ** 9)
    
    class MockEth:
        def __init__(self):
            self.block_number = 1000000
        
        def get_transaction_count(self, address):
            return 0
        
        def send_raw_transaction(self, tx):
            return b'0x' + b'1234567890abcdef' * 4
        
        def wait_for_transaction_receipt(self, tx_hash, timeout=120):
            import time
            time.sleep(1)  # Simulate blockchain delay
            return {
                'transactionHash': tx_hash,
                'blockNumber': self.block_number + 1,
                'gasUsed': 50000,
                'status': 1,
            }
        
        def get_transaction_receipt(self, tx_hash):
            return {
                'transactionHash': tx_hash,
                'blockNumber': self.block_number,
                'gasUsed': 50000,
                'status': 1,
            }
    
    return MockWeb3()


def anchor_merkle_root(
    w3: Web3,
    merkle_root: str,
) -> Dict:
    """
    Anchor Merkle root to blockchain.
    
    Creates a transaction that stores the Merkle root hash on-chain.
    
    Args:
        w3: Web3 instance
        merkle_root: Merkle root hash (64 chars hex)
    
    Returns:
        Dict with transaction details
    """
    logger.info(f"Anchoring Merkle root: {merkle_root[:16]}...")
    
    if not settings.blockchain_private_key:
        logger.warning("No private key configured, using mock anchoring")
        return _mock_anchor(w3, merkle_root)
    
    # Get account from private key
    account = Account.from_key(settings.blockchain_private_key)
    address = account.address
    
    logger.info(f"Using address: {address}")
    
    # Prepare transaction
    nonce = w3.eth.get_transaction_count(address)
    
    # Transaction data: Store Merkle root in transaction data field
    tx_data = "0x" + merkle_root
    
    transaction = {
        'nonce': nonce,
        'to': settings.blockchain_contract_address or address,  # Send to self if no contract
        'value': 0,  # No value transfer
        'gas': settings.max_gas_limit,
        'gasPrice': w3.to_wei(settings.gas_price_gwei, 'gwei'),
        'data': tx_data,
        'chainId': w3.eth.chain_id,
    }
    
    # Sign transaction
    signed_tx = account.sign_transaction(transaction)
    
    # Send transaction
    logger.info("Sending transaction...")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_hash_hex = w3.to_hex(tx_hash)
    
    logger.info(f"Transaction sent: {tx_hash_hex}")
    logger.info("Waiting for confirmation...")
    
    # Wait for confirmation
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    
    if receipt['status'] != 1:
        raise Exception(f"Transaction failed: {tx_hash_hex}")
    
    logger.info(f"Transaction confirmed in block: {receipt['blockNumber']}")
    
    return {
        "transaction_id": tx_hash_hex,
        "block_number": receipt['blockNumber'],
        "gas_used": receipt['gasUsed'],
        "gas_price_gwei": settings.gas_price_gwei,
    }


def _mock_anchor(w3: Web3, merkle_root: str) -> Dict:
    """Mock anchoring for development."""
    logger.warning("MOCK: Simulating blockchain anchoring (no real transaction)")
    
    # Simulate blockchain delay
    time.sleep(2)
    
    # Generate fake transaction ID
    import hashlib
    fake_tx = "0x" + hashlib.sha256(merkle_root.encode()).hexdigest()
    
    return {
        "transaction_id": fake_tx,
        "block_number": w3.eth.block_number + 1,
        "gas_used": 50000,
        "gas_price_gwei": settings.gas_price_gwei,
    }


def verify_transaction(w3: Web3, tx_id: str) -> Dict:
    """
    Verify transaction on blockchain.
    
    Args:
        w3: Web3 instance
        tx_id: Transaction ID
    
    Returns:
        Dict with transaction details
    """
    try:
        receipt = w3.eth.get_transaction_receipt(tx_id)
        
        if not receipt:
            return {
                "valid": False,
                "error": "Transaction not found"
            }
        
        return {
            "valid": True,
            "transaction_id": tx_id,
            "block_number": receipt['blockNumber'],
            "status": "success" if receipt['status'] == 1 else "failed",
            "gas_used": receipt['gasUsed'],
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }
