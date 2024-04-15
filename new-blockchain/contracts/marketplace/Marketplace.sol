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
        bool isCompleted;
        bool isErrored;
        uint64 startedAt;
        uint64 endedAt;
        uint64 totalTimesEstimate;
        uint64 totalTimesInUse;
        string rateDollarPerHour;
        string ipfsHash;
        string endReason;
    }

    mapping(string => RentStruct) public _rentData;

    event RegisterRentEvent(
        string indexed id,
        address builder,
        address provider,
        uint64 startedAt,
        uint64 totalTimesEstimate,
        string rateDollarPerHour,
        string rentURI
    );

    event EndRentEvent(
        string indexed id,
        address builder,
        address provider,
        uint64 endedAt,
        uint64 totalTimesInUse,
        string ratePerHour,
        string endReason
    );

    event ResourceErrorEvent(
        string indexed id,
        address builder,
        address provider,
        uint64 endedAt,
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
        uint64 _startedAt,
        uint64 _totalTimeEstimate,
        string memory _rateDollarPerHour,
        string memory _ipfsHash
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
            false,
            false,
            _startedAt,
            0,
            _totalTimeEstimate,
            0,
            _rateDollarPerHour,
            _ipfsHash,
            ""
        );

        emit RegisterRentEvent(
            _id,
            _builder,
            _provider,
            _startedAt,
            _totalTimeEstimate,
            _rateDollarPerHour,
            _ipfsHash
        );
    }

    function multiRegisterRent(
        string[] memory _ids,
        address _builder,
        address[] memory _providers,
        uint64[] memory _startedAt,
        uint64[] memory _totalTimeEstimate,
        string[] memory _rateDollarPerHour,
        string[] memory _ipfsHash
    ) public {
        uint256 length = _ids.length;
        require(
            _providers.length == length &&
                _startedAt.length == length &&
                _totalTimeEstimate.length == length &&
                _rateDollarPerHour.length == length &&
                _ipfsHash.length == length,
            "All arrays must have the same length"
        );

        require(_builder != address(0), "Not address 0");
        for (uint i = 0; i < _ids.length; i++) {
            require(
                _rentData[_ids[i]].builder == address(0) ||
                    _rentData[_ids[i]].provider == address(0),
                "Already registered"
            );
            _rentData[_ids[i]] = RentStruct(
                _builder,
                _providers[i],
                false,
                false,
                _startedAt[i],
                0,
                _totalTimeEstimate[i],
                0,
                _rateDollarPerHour[i],
                _ipfsHash[i],
                ""
            );

            emit RegisterRentEvent(
                _ids[i],
                _builder,
                _providers[i],
                _startedAt[i],
                _totalTimeEstimate[i],
                _rateDollarPerHour[i],
                _ipfsHash[i]
            );
        }
    }

    function finishRent(string memory _id, uint64 _endedAt) public {
        require(
            _rentData[_id].builder != address(0) &&
                _rentData[_id].provider != address(0),
            "Not registered"
        );
        require(_rentData[_id].isCompleted == false, "Already completed");
        require(_rentData[_id].isErrored == false, "Already stop");

        _rentData[_id].isCompleted = true;
        _rentData[_id].endedAt = _endedAt;
        _rentData[_id].endReason = "End rent resource";
        _rentData[_id].totalTimesInUse = _endedAt - _rentData[_id].startedAt;

        emit EndRentEvent(
            _id,
            _rentData[_id].builder,
            _rentData[_id].provider,
            _endedAt,
            _rentData[_id].totalTimesInUse,
            _rentData[_id].rateDollarPerHour,
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
        _rentData[_id].endedAt = uint64(block.timestamp);
        _rentData[_id].endReason = reason;
        _rentData[_id].totalTimesInUse = 0;

        emit ResourceErrorEvent(
            _id,
            _rentData[_id].builder,
            _rentData[_id].provider,
            uint64(block.timestamp),
            reason
        );
    }
}
