// SPDX-License-Identifier: MIT

pragma solidity 0.8.16;
import "interfaces/balancer/vault/IVault.sol";
import "interfaces/balancer/pool-weighted/IWeightedPoolFactoryV4.sol";
import "interfaces/balancer/pool-stable/IComposableStableFactoryV4.sol";
import "interfaces/balancer/pool-weighted/IWeightedPool.sol";
import "interfaces/balancer/pool-stable/IComposableStablePool.sol";



/**
 * @title The MaxiPoolCreationHelperV1
 * @author tritium.eth
 * @notice This contract attempts to make creating and initializing a pool easier from etherscan.
 */
contract WeightedPoolInitHelper {
    IVault public immutable vault;
    IWeightedPoolFactoryV4 public immutable weightedFactory;
    IComposableStableFactoryV4 public immutable stableFactory;
    address public constant DAO = 0xBA1BA1ba1BA1bA1bA1Ba1BA1ba1BA1bA1ba1ba1B;
    uint256 public constant defaultTokenRateCacheDuration = 21600;

    constructor(IVault _vault, IWeightedPoolFactoryV4 _weightedFactory, IComposableStableFactoryV4 _stableFactory ) {
        vault = _vault;
        weightedFactory = _weightedFactory;
        stableFactory = _stableFactory;
    }


    /**
     * @notice Easy Creation of a V4 weighted pool - using the factory directly saves a little gas
     * @param name The Long Name of the pool token - Normally like Balancer B-33WETH-33WBTC-34USDC Token - MAX 67 characters if you want a gauge
     * @param symbol The symbol - Normally like B-33WETH-33WBTC-34USDC  - Max 40 characters if you want a gauge
     * @param tokens An list of token addresses in the pool in ascending order (from 0 to f) - check the read functions
     * @param weightsFrom100 A list of token weights in percentage points ordered by the token addresses above (adds up to 100)
     * @param ExemptFees_supports_empty_list_to_default Speak with the Maxis about how to use this if your pool includes other boosted BPTs.  Otherwise set to an empty list
     * @param rateProviders_supports_empty_list_to_default An ordered list of rateProviders using zero addresses where there is none, or an empty array [] to autofill zeros for all rate providers.
     * @param weiAmountsPerToken An ordered list of amounts (wei denominated) of tokens for the initial deposit.  This will define opening prices. You  must have open approvals for each token to the vault.
     * @param swapFeeBPS The swap fee expressed in basis points from 1 to 1000 (0.01 - 10%)
     * @return The address of the created pool
    */
    function createAndJoinWeightedPool(
        string memory name,
        string memory symbol,
        address[] memory tokens,
        address[] memory rateProviders_supports_empty_list_to_default,
        bool[] memory ExemptFees_supports_empty_list_to_default,
        uint256[] memory weiAmountsPerToken,
        uint256[] memory  weightsFrom100,
        uint256 swapFeeBPS,
        bytes32 somethingRandomForSalt
    ) public returns (address) {
        address poolAddress = createWeightedPool(name, symbol, tokens, rateProviders_supports_empty_list_to_default,  weightsFrom100, swapFeeBPS, somethingRandomForSalt);
        IWeightedPool pool = IWeightedPool(poolAddress);
        bytes32 poolId = pool.getPoolId();
        initJoinWeightedPool(poolId, tokens, weiAmountsPerToken);
        return poolAddress;
    }

    /**
      * @notice Init Joins an empty pool to set the starting price
     * @param poolId the pool id of the pool to init join
     * @param tokenAddresses a list of all the tokens in the pool, sorted from lowest to highest (0 to F)
     * @param amountsPerToken a list of amounts such that a matching index returns a token/amount pair
     */
    function initJoinWeightedPool(
        bytes32 poolId,
        address[] memory tokenAddresses,
        uint256[] memory amountsPerToken
    ) public {
        require(tokenAddresses.length == amountsPerToken.length, "Arrays of different length");
        IAsset[] memory tokens = toIAssetArray(tokenAddresses);

        // The 0 as the first argument represents an init join
        bytes memory userData = abi.encode(0, amountsPerToken);

        // Construct the JoinPoolRequest struct
        IVault.JoinPoolRequest memory request = IVault.JoinPoolRequest({
            assets: tokens,
            maxAmountsIn: amountsPerToken,
            userData: userData,
            fromInternalBalance: false
        });

        // Call the joinPool function
        for (uint8 i=0; i < tokenAddresses.length; i++) {
            IERC20 t = IERC20(tokenAddresses[i]);
            t.transferFrom(msg.sender, address(this), amountsPerToken[i]);
            t.approve(address(vault), amountsPerToken[i]);
        }
        vault.joinPool(poolId, address(this), msg.sender, request);
    }


    /**
      * @notice Easy Creation of a V4 weighted pool - using the factory directly saves a little gas
     * @param name The Long Name of the pool token - Normally like Balancer B-33WETH-33WBTC-34USDC Token
     * @param symbol The symbol - Normally like B-33WETH-33WBTC-34USDC
     * @param tokens An list of token addresses in the pool in ascending order (from 0 to f) - check the read functions
     * @param weightsFrom100 A list of token weights in percentage points ordered by the token addresses above (adds up to 100)
     * @param rateProviders A list of rateProviders using zero addresses where there is none, or an empty array [] to autofill zeros for all rate providers.
     * @param swapFeeBPS The swap fee expressed in basis ponts from 1 to 1000 (0.01 - 10%)
     * @return The address of the created pool
    */
    function createWeightedPool(
        string memory  name,
        string memory  symbol,
        address[] memory tokens,
        address[] memory rateProviders,
        uint256[] memory weightsFrom100,
        uint256 swapFeeBPS,
        bytes32 somethingRandomForSalt
    ) public returns (address) {
        // Check Stuff
        uint len = tokens.length;
        require(len <= 8, "Weighted pools can support max 8 tokens");
        require(len == weightsFrom100.length, "weightsFrom 100 not same len as tokens");
        require(len == rateProviders.length || rateProviders.length == 0, "rateProviders  not same len as tokens");

        // Transform Weights
        uint256 totalWeight;
        for (uint i=0; i < len; i++) {
            weightsFrom100[i] = weightsFrom100[i] * 10 **16; // not renaming var to save local stack space
            totalWeight += weightsFrom100[i];
        }
        require(totalWeight == 1e18, "Total Pool Weight does not add up to 100");

        // Replace empty array with zeroed out rate providers
        bool emptyRateProviders = rateProviders.length == 0;
        address[] memory RateProviders = new address[](len);
        if(!emptyRateProviders){
            RateProviders = rateProviders;
        }
        require(RateProviders.length == len);
        // Transform Fees
        require(swapFeeBPS >=1  && swapFeeBPS <= 1000, "Fees must be between 0.01%(1 BPS) and 10%(1000 BPS)");
        return  weightedFactory.create(name, symbol, tokens, weightsFrom100, RateProviders, swapFeeBPS * 10 ** 14, DAO, somethingRandomForSalt);
    }


    /**
      * @notice Easy Creation of a V4 stable swap pool - using the factory directly saves a little gas
     * @param name The Long Name of the pool token - Normally like Balancer B-33WETH-33WBTC-34USDC Token - MAX 67 characters if you want a gauge
     * @param symbol The symbol - Normally like B-33WETH-33WBTC-34USDC  - Max 40 characters if you want a gauge
     * @param tokens An list of token addresses in the pool in ascending order (from 0 to f) - check the read functions.
     * @param amplificationParameter Also known as the A factor.  Defines how fast the pool slips when off balance.  Recommend <50 if you don't know what you are doing.
     * @param exemptFees_supports_empty_list_to_default Speak with the Maxis about how to use this if your pool includes other boosted BPTs.  Otherwise set to an empty list
     * @param rateProviders_supports_empty_list_to_default An ordered list of rateProviders using zero addresses where there is none, or an empty array [] to autofill zeros for all rate providers.
     * @param weiAmountsPerToken An ordered list of amounts (wei denominated) of tokens for the initial deposit.  This will define opening prices. You  must have open approvals for each token to the vault.
     * @param swapFeeBPS The swap fee expressed in basis points from 1 to 1000 (0.01 - 10%)
     * @return The address of the created pool
   */
function CreateStablePool(
    string memory name,
    string memory symbol,
    address[] memory tokens,
    uint256 amplificationParameter,
    address[] memory rateProviders_supports_empty_list_to_default,
    bool[] memory exemptFees_supports_empty_list_to_default,
    uint256[] memory weiAmountsPerToken,
    uint256 swapFeeBPS,
    bytes32 somethingRandomForSalt
) public returns (address) {
    // Check Stuff
    uint len = tokens.length;
    require(len <= 5, "Stable pools can only spport max 5 tokens");
    require(len == rateProviders_supports_empty_list_to_default.length || rateProviders_supports_empty_list_to_default.length == 0, "rateProviders  not same len as tokens or empty");
    require(len == exemptFees_supports_empty_list_to_default.length || exemptFees_supports_empty_list_to_default.length == 0, "ExemptFees not same len as tokens or empty");
    require(amplificationParameter > 1, "A Factor must be over 1");
    require(amplificationParameter < 2000, "This interface does not support creating pools with A-factor over 2000, you can use the factory directly");
    require(bytes(symbol).length <= 26, "Symbols with more than 26 characters break gauge creation");
    require(bytes(symbol).length >= 6, "You can do better than that on the symbol name.  BPT-80XXX-20YYY");
    require(bytes(name).length >= 10, "Use more than 10 characters and less than around 60 in your pool name");


    // pack tokenRateCacheDurations with default
    uint256[] memory tokenRateCacheDurations = new uint256[](tokens.length);
    for (uint i; i < tokenRateCacheDurations.length; ++i) tokenRateCacheDurations[i] = defaultTokenRateCacheDuration;

    // Handle fees empty list default
    if(exemptFees_supports_empty_list_to_default.length == 0){
        exemptFees_supports_empty_list_to_default = new bool[](tokens.length);
    }

    // Use rateProviders_supports_empty_list_to_default if not empty
    require(rateProviders_supports_empty_list_to_default.length == len);
    // Transform Fees
    require(swapFeeBPS >=1  && swapFeeBPS <= 1000, "Fees must be between 0.01%(1 BPS) and 10%(1000 BPS)");
    return  stableFactory.create(name, symbol, tokens, amplificationParameter, rateProviders_supports_empty_list_to_default, tokenRateCacheDurations, exemptFees_supports_empty_list_to_default, swapFeeBPS * 10 ** 14, DAO, somethingRandomForSalt);
}


        /**
      * @notice Init Joins an empty pool to set the starting price
     * @param poolId the pool id of the pool to init join
     * @param tokenAddresses a list of all the tokens in the pool, sorted from lowest to highest (0 to F) - You must also include the BPT token of the pool itself, can have amount 0
     * @param amountsPerToken a list of amounts such that a matching index returns a token/amount pair - Can use zero for own BPT
     */
    function initJoinStableSwap(
        bytes32 poolId,
        address poolAddress,
        address[] memory tokenAddresses,
        uint256[] memory amountsPerToken
    ) public {
        require(tokenAddresses.length == amountsPerToken.length, "Arrays of different length");
        /// TODO consider a check around balanced deposits
        bool foundOwnToken;

        for(uint8 i=0; i<tokenAddresses.length;){
            if (tokenAddresses[i] == poolAddress){
                amountsPerToken[i] = 2**111;
                foundOwnToken = true;
            }
        }

        require(foundOwnToken, "You must include the address of the pools own BPT in the sorted list of addresses.  You can set it's amount to 0");

        IAsset[] memory tokens = toIAssetArray(tokenAddresses);

        // The 0 as the first argument represents an init join
        bytes memory userData = abi.encode(0, amountsPerToken);

        // Construct the JoinPoolRequest struct
        IVault.JoinPoolRequest memory request = IVault.JoinPoolRequest({
            assets: tokens,
            maxAmountsIn: amountsPerToken,
            userData: userData,
            fromInternalBalance: false
        });

        // Call the joinPool function
        for (uint8 i=0; i < tokenAddresses.length; i++) {
            if(tokenAddresses[i] != poolAddress) {
                IERC20 t = IERC20(tokenAddresses[i]);
                t.transferFrom(msg.sender, address(this), amountsPerToken[i]);
                t.approve(address(vault), amountsPerToken[i]);
            }
        }
        vault.joinPool(poolId, address(this), msg.sender, request);
    }

    /**
     * @notice Converts an array of token addresses to an array of IAsset objects
     * @param tokenAddresses the array of token addresses to convert
     * @return the array of IAsset objects
     */
    function toIAssetArray(address[] memory tokenAddresses) private pure returns (IAsset[] memory) {
        IAsset[] memory assets = new IAsset[](tokenAddresses.length);
        for (uint256 i = 0; i < tokenAddresses.length; i++) {
            assets[i] = IAsset(tokenAddresses[i]);
        }
        return assets;
    }


    function sortAmountsByAddresses(address[] memory addresses, uint256[] memory amounts) public pure returns (address[] memory, uint256[] memory) {
    uint256 n = addresses.length;
    for (uint256 i = 0; i < n - 1; i++) {
        for (uint256 j = 0; j < n - i - 1; j++) {
            if (addresses[j] > addresses[j + 1]) {
                address tempAddress = addresses[j];
                addresses[j] = addresses[j + 1];
                addresses[j + 1] = tempAddress;
                uint256 tempAmount = amounts[j];
                amounts[j] = amounts[j + 1];
                amounts[j + 1] = tempAmount;
            }
        }
    }
    return (addresses, amounts);
    }

    function sortWeightedCreateDataByAddress(address[] memory addresses, address[] memory rateProviders, uint256[] memory amounts, uint256[] memory weights) public pure returns (address[] memory, address[] memory, uint256[] memory, uint256[] memory) {
    uint256 n = addresses.length;
    for (uint256 i = 0; i < n - 1; i++) {
        for (uint256 j = 0; j < n - i - 1; j++) {
            if (addresses[j] > addresses[j + 1]) {
                address tempAddress = addresses[j];
                addresses[j] = addresses[j + 1];
                addresses[j + 1] = tempAddress;
                uint256 tempAmount = amounts[j];
                amounts[j] = amounts[j + 1];
                amounts[j + 1] = tempAmount;
                uint256 tempWeight = weights[j];
                weights[j] = weights[j + 1];
                weights[j + 1] = tempWeight;
                address tempRateProvider = rateProviders[j];
                rateProviders[j] = rateProviders[j + 1];
                rateProviders[j + 1] = tempRateProvider;
            }
        }
    }
    return (addresses, rateProviders, amounts, weights);
    }
}




