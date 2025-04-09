// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/IFedToken.sol";

contract FedToken is ERC20, Ownable, IFedToken {
    uint256 public constant INITIAL_SUPPLY = 100000000 * 10**18;

    constructor() ERC20("FedChain Token", "FCT") {
        _mint(msg.sender, INITIAL_SUPPLY);
    }

    function mint(address to, uint256 amount) external override onlyOwner {
        _mint(to, amount);
    }

    // Explicitly override functions that exist in both ERC20 and IFedToken
    function balanceOf(address account) public view override(ERC20, IFedToken) returns (uint256) {
        return super.balanceOf(account);
    }

    function transfer(address to, uint256 amount) public override(ERC20, IFedToken) returns (bool) {
        return super.transfer(to, amount);
    }

    function transferFrom(address from, address to, uint256 amount) public override(ERC20, IFedToken) returns (bool) {
        return super.transferFrom(from, to, amount);
    }
}
