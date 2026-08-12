pragma solidity ^0.8.18;

contract Voting {
    mapping ( address => bool ) allowed;
    mapping ( address => bool ) voted;

    uint approve_count;
    uint reject_count;
    uint majority;

    bool ended;
    bool approved;

    constructor ( address[] memory _voters ) {
        require ( _voters.length % 2 == 1, "Even number of voters." );

        for ( uint i = 0; i < _voters.length; i++ ) {
            allowed[_voters[i]] = true;
        }

        majority = _voters.length / 2 + 1;
    }

    modifier can_vote {
        // Checked before the address: every attempt after the conclusion is
        // answered with "Voting ended.", even one from a stranger.
        require ( !ended, "Voting ended." );
        require ( allowed[msg.sender], "Invalid address." );
        require ( !voted[msg.sender], "Already voted." );
        _;
    }

    function vote_approve ( ) external can_vote {
        voted[msg.sender] = true;
        approve_count += 1;

        if ( approve_count >= majority ) {
            ended    = true;
            approved = true;
        }
    }

    function vote_reject ( ) external can_vote {
        voted[msg.sender] = true;
        reject_count += 1;

        if ( reject_count >= majority ) {
            ended    = true;
            approved = false;
        }
    }

    function status ( ) external view returns ( bool, bool ) {
        return ( ended, approved );
    }
}
