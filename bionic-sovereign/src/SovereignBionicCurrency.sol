// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title SovereignBionicCurrency
/// @notice ERC-20 with real EIP-2612 gasless permit + sovereign mint authority.
/// @dev Self-contained (no external libs) so it compiles with stock solc.
contract SovereignBionicCurrency {
    string public constant name = "Sovereign Bionic Network";
    string public constant symbol = "BIONIC";
    uint8 public constant decimals = 18;

    uint256 public totalSupply;
    address public authority;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    mapping(address => uint256) public nonces;

    // ---- EIP-712 domain separator (computed once at deploy) ----
    bytes32 public immutable DOMAIN_SEPARATOR;
    // keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)")
    bytes32 public constant PERMIT_TYPEHASH =
        0x6e71edae12b1b97f4d1f60370fef10105fa2faae0126114a169c64845d6126c9;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event SovereignMint(address indexed to, uint256 amount, bytes32 indexed authorizationRef);
    event GaslessSettlement(address indexed owner, address indexed to, uint256 value, address indexed relayer);

    error NotAuthority();
    error PermitExpired();
    error BadSignature();
    error InsufficientBalance();

    event AuthorityTransferred(address indexed oldAuthority, address indexed newAuthority);

    constructor(address authority_) {
        authority = authority_;
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
                keccak256(bytes(name)),
                keccak256(bytes("1")),
                block.chainid,
                address(this)
            )
        );
        // Genesis allocation: 1B tokens
        _mint(authority_, 1_000_000_000e18, bytes32("GENESIS_BLOCK"));
    }

    modifier onlyAuthority() {
        if (msg.sender != authority) revert NotAuthority();
        _;
    }

    /// @notice Hand sovereign mint authority to another contract (e.g. the curve).
    function transferAuthority(address newAuthority) external onlyAuthority {
        address old = authority;
        authority = newAuthority;
        emit AuthorityTransferred(old, newAuthority);
    }

    function _mint(address to, uint256 amount, bytes32 ref) internal {
        totalSupply += amount;
        balanceOf[to] += amount;
        emit Transfer(address(0), to, amount);
        emit SovereignMint(to, amount, ref);
    }

    /// @notice Sovereign minting controlled by master authority.
    function sovereignMint(address to, uint256 amount, bytes32 authRef) external onlyAuthority {
        _mint(to, amount, authRef);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        _transfer(msg.sender, to, value);
        return true;
    }

    function approve(address spender, uint256 value) external returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        uint256 allowed = allowance[from][msg.sender];
        if (allowed != type(uint256).max) {
            if (allowed < value) revert InsufficientBalance();
            unchecked { allowance[from][msg.sender] = allowed - value; }
        }
        _transfer(from, to, value);
        return true;
    }

    function _transfer(address from, address to, uint256 value) internal {
        uint256 bal = balanceOf[from];
        if (bal < value) revert InsufficientBalance();
        unchecked {
            balanceOf[from] = bal - value;
            balanceOf[to] += value;
        }
        emit Transfer(from, to, value);
    }

    // ---- REAL EIP-2612 permit (standard, recover via ecrecover) ----

    /// @notice Recover the signer of the permit struct hash.
    function recoverSigner(
        address owner, address spender, uint256 value, uint256 deadline,
        uint8 v, bytes32 r, bytes32 s
    ) public view returns (address) {
        bytes32 structHash = keccak256(
            abi.encode(PERMIT_TYPEHASH, owner, spender, value, nonces[owner], deadline)
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, structHash));
        return ecrecover(digest, v, r, s);
    }

    /// @notice Gasless approval via off-chain EIP-712 signature.
    function permit(
        address owner, address spender, uint256 value, uint256 deadline,
        uint8 v, bytes32 r, bytes32 s
    ) public {
        if (block.timestamp > deadline) revert PermitExpired();
        address signer = recoverSigner(owner, spender, value, deadline, v, r, s);
        if (signer != owner || owner == address(0)) revert BadSignature();
        unchecked { nonces[owner]++; }
        allowance[owner][spender] = value;
        emit Approval(owner, spender, value);
    }

    /// @notice Relayer-executed gasless settlement: verifies permit sig and
    ///         transfers atomically in one call. Sender pays zero gas.
    function executeGaslessSettlement(
        address owner, address to, uint256 value, uint256 deadline,
        uint8 v, bytes32 r, bytes32 s
    ) external {
        permit(owner, address(this), value, deadline, v, r, s);
        _transfer(owner, to, value);
        emit GaslessSettlement(owner, to, value, msg.sender);
    }
}
