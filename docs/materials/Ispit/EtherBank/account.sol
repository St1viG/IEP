pragma solidity ^0.8.18;

contract Account {
    address payable owner;
    uint256 balance;

    modifier only_owner {
        require ( msg.sender == owner, "Only owner can execute this transaction!" );
        _;
    }

    constructor ( address payable _owner ) {
        owner = _owner;
    }

    function get_balance ( ) external view only_owner returns ( uint256 ) {
        return balance;
    }

    function deposit ( ) external payable only_owner {
        balance += msg.value;
    }

    function withdraw ( address payable to, uint256 amount ) external payable only_owner {
        require ( balance >= amount, "Insufficient funds!" );
        balance -= amount;
        to.transfer ( amount );
    }
}
