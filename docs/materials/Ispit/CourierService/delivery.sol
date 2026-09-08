pragma solidity ^0.8.18;

contract Delivery {
    address payable owner_address;
    address payable courier_address;
    address customer_address;
    uint delivery_price;
    bool paid;
    bool delivered;

    constructor ( address payable _owner_address, address payable _courier_address, address _customer_address, uint _delivery_price ) {
        owner_address    = _owner_address;
        courier_address  = _courier_address;
        customer_address = _customer_address;
        delivery_price   = _delivery_price;

    }

    function pay ( ) external payable {
        require ( msg.sender == customer_address, "Invalid customer address!" );
        require ( msg.value == delivery_price, "Insufficient funds!" );
        require ( paid == false, "Delivery already payed!" );

        paid = true;
    }

    function confirm_delivery ( ) external payable {
        require ( msg.sender == customer_address, "Invalid cusotmer address!" );
        require ( paid == true, "Delivery not paid!" );
        require ( delivered == false , "Delivery already confirmed!" );

        delivered = true;

        uint owner_amount = delivery_price / 2;
        uint courier_amount = delivery_price - owner_amount;

        owner_address.transfer ( owner_amount );
        courier_address.transfer ( courier_amount );
    }
}
