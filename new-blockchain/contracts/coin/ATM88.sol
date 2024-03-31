// SPDX-License-Identifier: MIT

pragma solidity >=0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract ATM88 is ERC20, Ownable, Pausable {
    constructor() ERC20("USDT", "USDT") {
        _mint(_msgSender(), 100_000_000 * 10 ** 18);

    }

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
}
