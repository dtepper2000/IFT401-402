<?php 
if(isset($_POST['submit'])){
    $to = "progettocinquantuno@gmail.com"; // this is your Email address
    $from = $_POST['email']; // this is the sender's Email address
    $subject = "Newsletter Subscription";
    $message =" Thanks for Subscription";

    $headers = "From:" . $from;
    $headers2 = "From:" . $to;
    mail($to,$subject,$message,$headers);
    // echo "Mail Sent. Thank you " .  "we will contact you shortly.";
    header('Location: thanks.html');
    // You cannot use header and echo together. It's one or the other.
    }
    
?>