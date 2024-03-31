// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

import "@openzeppelin/contracts-upgradeable/token/ERC721/extensions/ERC721URIStorageUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/utils/CountersUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/security/PausableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";

contract Marketplace is OwnableUpgradeable, PausableUpgradeable {
    struct RentStruct {
        address builder;
        address provider;
        uint256 startedAt;
        uint256 endedAt;
        bool isCompleted;
        bool isErrored;
        string ratePerHour;
        string totalHours;
        string rentURI;
        string endReason;
    }

    mapping(string => RentStruct) public _rentData;

    event RegisterRentEvent(
        address builder,
        address provider,
        uint256 startedAt,
        string ratePerHour,
        string totalHours,
        string id,
        string rentURI
    );

    event EndRentEvent(
        address builder,
        address provider,
        uint256 endedAt,
        string ratePerHour,
        string totalHours,
        string id,
        string endReason
    );

    event ResourceErrorEvent(
        address builder,
        address provider,
        uint256 endedAt,
        string id,
        string endReason
    );

    function initialize() public virtual initializer {
        __Ownable_init();
        __Pausable_init();
    }

    function registerRent(
        string memory _id,
        address _builder,
        address _provider,
        string memory _ratePerHour,
        string memory _totalHours,
        string memory _rentURI
    ) public {
        require(
            _builder != address(0) && _provider != address(0),
            "Not address 0"
        );
        require(
            _rentData[_id].builder == address(0) ||
                _rentData[_id].provider == address(0),
            "Already registered"
        );
        _rentData[_id] = RentStruct(
            _builder,
            _provider,
            block.timestamp,
            0,
            false,
            false,
            _ratePerHour,
            _totalHours,
            _rentURI,
            ""
        );

        emit RegisterRentEvent(
            _builder,
            _provider,
            block.timestamp,
            _ratePerHour,
            _totalHours,
            _id,
            _rentURI
        );
    }

    function finishRent(string memory _id, string memory _totalHours) public {
        require(
            _rentData[_id].builder != address(0) &&
                _rentData[_id].provider != address(0),
            "Not registered"
        );
        require(_rentData[_id].isCompleted == false, "Already completed");
        require(_rentData[_id].isErrored == false, "Already stop");

        _rentData[_id].isCompleted = true;
        _rentData[_id].endedAt = block.timestamp;
        _rentData[_id].endReason = "End rent resource";
        _rentData[_id].totalHours = _totalHours;

        emit EndRentEvent(
            _rentData[_id].builder,
            _rentData[_id].provider,
            block.timestamp,
            _rentData[_id].ratePerHour,
            _totalHours,
            _id,
            "End rent resource"
        );
    }

    function resourceError(string memory _id, string memory reason) public {
        require(
            _rentData[_id].builder != address(0) &&
                _rentData[_id].provider != address(0),
            "Not registered"
        );
        require(_rentData[_id].isCompleted == false, "Already completed");
        require(_rentData[_id].isErrored == false, "Already stop");

        _rentData[_id].isErrored = true;
        _rentData[_id].endedAt = block.timestamp;
        _rentData[_id].endReason = reason;
        _rentData[_id].totalHours = "0";

        emit ResourceErrorEvent(
            _rentData[_id].builder,
            _rentData[_id].provider,
            block.timestamp,
            _id,
            reason
        );
    }
}
