// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import {SovereignBionicCurrency} from "../src/SovereignBionicCurrency.sol";
import {BondingCurveAMM} from "../src/BondingCurveAMM.sol";

contract Deploy is Script {
    function run() external {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerKey);

        address dad = vm.addr(deployerKey);
        SovereignBionicCurrency token = new SovereignBionicCurrency(dad);
        BondingCurveAMM curve = new BondingCurveAMM(
            address(token),
            10_000_000e18, // virtual token reserve
            500_000e18     // initial base reserve
        );

        console.log("Dad authority:  ", dad);
        console.log("BIONIC token:   ", address(token));
        console.log("BondingCurve:   ", address(curve));

        vm.stopBroadcast();
    }
}
