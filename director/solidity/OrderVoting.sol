pragma solidity ^0.8.18;

contract OrderVoting {
    event VoteCast ( address indexed voter, bool approved );
    event VotingFinished ( bool approved );

    address[] public voters;
    mapping ( address => bool ) public is_voter;
    mapping ( address => bool ) public has_voted;

    uint256 public approve_count;
    uint256 public reject_count;
    uint256 public majority; // n / 2 + 1

    bool public finished;
    bool public result;

    modifier only_voter ( ) {
        require ( is_voter[msg.sender], "Invalid address." );
        _;
    }

    modifier not_voted ( ) {
        require ( !has_voted[msg.sender], "Already voted." );
        _;
    }

    modifier voting_active ( ) {
        require ( !finished, "Voting ended." );
        _;
    }

    constructor ( address[] memory _voters ) {
        require ( _voters.length > 0, "Voters required." );
        require ( _voters.length % 2 == 1, "Even number of voters." );

        for ( uint256 i = 0; i < _voters.length; i++ ) {
            address voter = _voters[i];

            require ( voter != address ( 0 ), "Invalid address." );
            require ( !is_voter[voter], "Voter not unique." );

            is_voter[voter] = true;
            voters.push ( voter );
        }

        majority = _voters.length / 2 + 1;
    }

    function approve ( )
        external
        voting_active
        only_voter
        not_voted
    {
        has_voted[msg.sender] = true;
        approve_count += 1;

        emit VoteCast ( msg.sender, true );

        if ( approve_count >= majority ) {
            finished = true;
            result = true;

            emit VotingFinished ( true );
        }
    }

    function reject ( )
        external
        voting_active
        only_voter
        not_voted
    {
        has_voted[msg.sender] = true;
        reject_count += 1;

        emit VoteCast ( msg.sender, false );

        if ( reject_count >= majority ) {
            finished = true;
            result = false;

            emit VotingFinished ( false );
        }
    }

    function get_voters ( ) public view returns ( address[] memory ) {
        return voters;
    }

    function get_state ( )
        public
        view
        returns (
            uint256 approvals,
            uint256 rejections,
            uint256 required,
            bool is_finished,
            bool is_approved
        )
    {
        return ( approve_count, reject_count, majority, finished, result );
    }
}
