// SPDX-License-Identifier: MIT
// Jencoins ICO

pragma solidity ^0.8.15;

contract jencoin_ico {
    // State variables
    uint64 public max_jencoins = 1e6;
    uint64 public usd_to_jencoins = 1000;
    uint64 public total_jencoins_allocated = 0;

    // Mappings are equivalent to python dictionaries.
    mapping(address => uint64) equity_jencoins;
    mapping(address => uint64) equity_usd;

    // Modifiers are equivalent to decorators in python
    modifier can_buy_jencoins(uint64 usd_to_invest) {
        require(
            usd_to_invest * usd_to_jencoins + total_jencoins_allocated <=
                max_jencoins
        );
        _;
    }

    // TODO: understand why this isn't redundant (can't just directly use mappings above)
    function equity_in_jencoins(address investor)
        external
        view
        returns (uint64)
    {
        return equity_jencoins[investor];
    }

    function equity_in_usd(address investor) external view returns (uint64) {
        return equity_usd[investor];
    }

    function buy_jencoins(address investor, uint64 usd_to_invest)
        external
        can_buy_jencoins(usd_to_invest)
    {
        uint64 jencoins_to_buy = usd_to_invest * usd_to_jencoins;
        equity_jencoins[investor] += jencoins_to_buy;
        equity_usd[investor] = equity_jencoins[investor] / usd_to_jencoins;

        total_jencoins_allocated += jencoins_to_buy;
    }

    function sell_jencoins(address investor, uint64 jencoins_to_sell) external {
        equity_jencoins[investor] -= jencoins_to_sell;
        equity_usd[investor] = equity_jencoins[investor] / usd_to_jencoins;

        total_jencoins_allocated -= jencoins_to_sell;
    }
}
