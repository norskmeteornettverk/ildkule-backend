<?php
http_response_code(404);
#credit to https://codepen.io/KeithPaul
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Siden er ikke funnet</title>
 
    <style>
@import url("https://fonts.googleapis.com/css2?family=Comic+Neue:wght@300&display=swap");
.wrapper {
  min-width: 100vw;
  min-height: 100vh;
  display: flex;
  flex-wrap: wrap;
  text-align: center;
  align-items: center;
  background: #eee;
}
.wrapper .text_group .text_404 {
  font-family: "Comic Neue", cursive;
  font-size: 10em;
  box-sizing: border-box;
  color: #363636;
}
.wrapper .text_group .text_lost {
  font-family: "Comic Neue", cursive;
  font-size: 2em;
  line-height: 50px;
  box-sizing: border-box;
  color: #565656;
}
.wrapper .window_group .window_404 {
  width: 200px;
  height: 350px;
  border-radius: 100px;
  box-shadow: -3px -3px 0px 5px #d4d4d4, 5px 5px 0px 2px white;
  background: linear-gradient(310deg, #020024 0%, #09096b 0%, black 80%);
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
}
.wrapper .window_group .window_404 .stars {
  width: 400px;
  height: 100%;
  position: absolute;
  top: 0;
  right: 0;
  animation: flyby 30s linear infinite;
}
.wrapper .window_group .window_404 .stars .star {
  border-radius: 50%;
  background: #ffffff;
  position: absolute;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(1) {
  width: 2px;
  height: 2px;
  left: 55px;
  top: 234px;
  animation: twinkle1 12s linear infinite;
  animation-delay: 10s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(1):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(2) {
  width: 2px;
  height: 2px;
  left: 122px;
  top: 291px;
  animation: twinkle2 11s linear infinite;
  animation-delay: 4s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(2):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(3) {
  width: 3px;
  height: 3px;
  left: 310px;
  top: 171px;
  animation: twinkle3 12s linear infinite;
  animation-delay: 6s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(3):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(4) {
  width: 1px;
  height: 1px;
  left: 380px;
  top: 199px;
  animation: twinkle4 8s linear infinite;
  animation-delay: 14s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(4):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(5) {
  width: 2px;
  height: 2px;
  left: 378px;
  top: 132px;
  animation: twinkle5 10s linear infinite;
  animation-delay: 8s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(5):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(6) {
  width: 1px;
  height: 1px;
  left: 188px;
  top: 232px;
  animation: twinkle6 6s linear infinite;
  animation-delay: 12s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(6):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(7) {
  width: 1px;
  height: 1px;
  left: 355px;
  top: 317px;
  animation: twinkle7 12s linear infinite;
  animation-delay: 5s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(7):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(8) {
  width: 1px;
  height: 1px;
  left: 64px;
  top: 63px;
  animation: twinkle8 11s linear infinite;
  animation-delay: 4s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(8):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(9) {
  width: 3px;
  height: 3px;
  left: 387px;
  top: 127px;
  animation: twinkle9 7s linear infinite;
  animation-delay: 15s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(9):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(10) {
  width: 2px;
  height: 2px;
  left: 167px;
  top: 66px;
  animation: twinkle10 9s linear infinite;
  animation-delay: 15s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(10):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(11) {
  width: 1px;
  height: 1px;
  left: 263px;
  top: 47px;
  animation: twinkle11 7s linear infinite;
  animation-delay: 13s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(11):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(12) {
  width: 1px;
  height: 1px;
  left: 365px;
  top: 241px;
  animation: twinkle12 6s linear infinite;
  animation-delay: 10s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(12):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(13) {
  width: 2px;
  height: 2px;
  left: 40px;
  top: 213px;
  animation: twinkle13 8s linear infinite;
  animation-delay: 11s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(13):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(14) {
  width: 3px;
  height: 3px;
  left: 211px;
  top: 61px;
  animation: twinkle14 10s linear infinite;
  animation-delay: 17s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(14):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(15) {
  width: 1px;
  height: 1px;
  left: 264px;
  top: 117px;
  animation: twinkle15 12s linear infinite;
  animation-delay: 8s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(15):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(16) {
  width: 2px;
  height: 2px;
  left: 193px;
  top: 96px;
  animation: twinkle16 11s linear infinite;
  animation-delay: 8s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(16):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(17) {
  width: 3px;
  height: 3px;
  left: 392px;
  top: 217px;
  animation: twinkle17 6s linear infinite;
  animation-delay: 13s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(17):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(18) {
  width: 3px;
  height: 3px;
  left: 300px;
  top: 290px;
  animation: twinkle18 12s linear infinite;
  animation-delay: 8s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(18):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(19) {
  width: 1px;
  height: 1px;
  left: 40px;
  top: 204px;
  animation: twinkle19 11s linear infinite;
  animation-delay: 4s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(19):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(20) {
  width: 3px;
  height: 3px;
  left: 168px;
  top: 201px;
  animation: twinkle20 12s linear infinite;
  animation-delay: 12s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(20):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(21) {
  width: 2px;
  height: 2px;
  left: 188px;
  top: 90px;
  animation: twinkle21 6s linear infinite;
  animation-delay: 12s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(21):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(22) {
  width: 2px;
  height: 2px;
  left: 305px;
  top: 325px;
  animation: twinkle22 12s linear infinite;
  animation-delay: 4s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(22):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(23) {
  width: 3px;
  height: 3px;
  left: 76px;
  top: 252px;
  animation: twinkle23 9s linear infinite;
  animation-delay: 18s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(23):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(24) {
  width: 3px;
  height: 3px;
  left: 286px;
  top: 312px;
  animation: twinkle24 13s linear infinite;
  animation-delay: 14s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(24):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(25) {
  width: 1px;
  height: 1px;
  left: 166px;
  top: 72px;
  animation: twinkle25 9s linear infinite;
  animation-delay: 8s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(25):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(26) {
  width: 3px;
  height: 3px;
  left: 142px;
  top: 116px;
  animation: twinkle26 9s linear infinite;
  animation-delay: 6s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(26):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(27) {
  width: 1px;
  height: 1px;
  left: 299px;
  top: 241px;
  animation: twinkle27 13s linear infinite;
  animation-delay: 5s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(27):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(28) {
  width: 2px;
  height: 2px;
  left: 9px;
  top: 33px;
  animation: twinkle28 12s linear infinite;
  animation-delay: 7s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(28):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(29) {
  width: 3px;
  height: 3px;
  left: 117px;
  top: 8px;
  animation: twinkle29 11s linear infinite;
  animation-delay: 10s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(29):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(30) {
  width: 3px;
  height: 3px;
  left: 112px;
  top: 131px;
  animation: twinkle30 8s linear infinite;
  animation-delay: 10s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(30):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(31) {
  width: 3px;
  height: 3px;
  left: 368px;
  top: 93px;
  animation: twinkle31 12s linear infinite;
  animation-delay: 8s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(31):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(32) {
  width: 3px;
  height: 3px;
  left: 159px;
  top: 249px;
  animation: twinkle32 7s linear infinite;
  animation-delay: 15s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(32):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(33) {
  width: 3px;
  height: 3px;
  left: 196px;
  top: 277px;
  animation: twinkle33 13s linear infinite;
  animation-delay: 9s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(33):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(34) {
  width: 2px;
  height: 2px;
  left: 191px;
  top: 317px;
  animation: twinkle34 11s linear infinite;
  animation-delay: 13s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(34):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(35) {
  width: 1px;
  height: 1px;
  left: 294px;
  top: 322px;
  animation: twinkle35 13s linear infinite;
  animation-delay: 10s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(35):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(36) {
  width: 1px;
  height: 1px;
  left: 277px;
  top: 178px;
  animation: twinkle36 8s linear infinite;
  animation-delay: 18s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(36):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(37) {
  width: 2px;
  height: 2px;
  left: 128px;
  top: 267px;
  animation: twinkle37 10s linear infinite;
  animation-delay: 17s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(37):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(38) {
  width: 1px;
  height: 1px;
  left: 138px;
  top: 189px;
  animation: twinkle38 10s linear infinite;
  animation-delay: 18s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(38):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(39) {
  width: 2px;
  height: 2px;
  left: 271px;
  top: 289px;
  animation: twinkle39 7s linear infinite;
  animation-delay: 11s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(39):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(40) {
  width: 3px;
  height: 3px;
  left: 352px;
  top: 145px;
  animation: twinkle40 8s linear infinite;
  animation-delay: 14s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(40):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(41) {
  width: 2px;
  height: 2px;
  left: 97px;
  top: 303px;
  animation: twinkle41 7s linear infinite;
  animation-delay: 11s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(41):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(42) {
  width: 1px;
  height: 1px;
  left: 89px;
  top: 75px;
  animation: twinkle42 6s linear infinite;
  animation-delay: 10s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(42):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(43) {
  width: 1px;
  height: 1px;
  left: 179px;
  top: 341px;
  animation: twinkle43 9s linear infinite;
  animation-delay: 7s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(43):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(44) {
  width: 1px;
  height: 1px;
  left: 220px;
  top: 304px;
  animation: twinkle44 11s linear infinite;
  animation-delay: 16s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(44):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(45) {
  width: 1px;
  height: 1px;
  left: 313px;
  top: 74px;
  animation: twinkle45 9s linear infinite;
  animation-delay: 17s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(45):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(46) {
  width: 3px;
  height: 3px;
  left: 356px;
  top: 276px;
  animation: twinkle46 8s linear infinite;
  animation-delay: 17s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(46):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(47) {
  width: 1px;
  height: 1px;
  left: 232px;
  top: 51px;
  animation: twinkle47 6s linear infinite;
  animation-delay: 16s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(47):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(48) {
  width: 2px;
  height: 2px;
  left: 97px;
  top: 334px;
  animation: twinkle48 9s linear infinite;
  animation-delay: 7s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(48):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(49) {
  width: 2px;
  height: 2px;
  left: 336px;
  top: 83px;
  animation: twinkle49 9s linear infinite;
  animation-delay: 13s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(49):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(50) {
  width: 1px;
  height: 1px;
  left: 132px;
  top: 75px;
  animation: twinkle50 7s linear infinite;
  animation-delay: 5s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(50):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(51) {
  width: 2px;
  height: 2px;
  left: 362px;
  top: 48px;
  animation: twinkle51 11s linear infinite;
  animation-delay: 8s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(51):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(52) {
  width: 1px;
  height: 1px;
  left: 121px;
  top: 34px;
  animation: twinkle52 7s linear infinite;
  animation-delay: 5s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(52):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(53) {
  width: 2px;
  height: 2px;
  left: 59px;
  top: 136px;
  animation: twinkle53 9s linear infinite;
  animation-delay: 9s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(53):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(54) {
  width: 2px;
  height: 2px;
  left: 389px;
  top: 12px;
  animation: twinkle54 13s linear infinite;
  animation-delay: 18s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(54):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(55) {
  width: 2px;
  height: 2px;
  left: 252px;
  top: 169px;
  animation: twinkle55 10s linear infinite;
  animation-delay: 9s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(55):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(56) {
  width: 2px;
  height: 2px;
  left: 27px;
  top: 107px;
  animation: twinkle56 12s linear infinite;
  animation-delay: 9s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(56):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(57) {
  width: 2px;
  height: 2px;
  left: 204px;
  top: 3px;
  animation: twinkle57 10s linear infinite;
  animation-delay: 11s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(57):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(58) {
  width: 2px;
  height: 2px;
  left: 4px;
  top: 219px;
  animation: twinkle58 13s linear infinite;
  animation-delay: 16s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(58):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(59) {
  width: 3px;
  height: 3px;
  left: 260px;
  top: 268px;
  animation: twinkle59 11s linear infinite;
  animation-delay: 8s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(59):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(60) {
  width: 2px;
  height: 2px;
  left: 300px;
  top: 234px;
  animation: twinkle60 10s linear infinite;
  animation-delay: 7s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(60):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(61) {
  width: 2px;
  height: 2px;
  left: 83px;
  top: 189px;
  animation: twinkle61 7s linear infinite;
  animation-delay: 11s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(61):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(62) {
  width: 2px;
  height: 2px;
  left: 32px;
  top: 113px;
  animation: twinkle62 12s linear infinite;
  animation-delay: 10s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(62):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(63) {
  width: 2px;
  height: 2px;
  left: 107px;
  top: 95px;
  animation: twinkle63 7s linear infinite;
  animation-delay: 9s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(63):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(64) {
  width: 2px;
  height: 2px;
  left: 232px;
  top: 154px;
  animation: twinkle64 13s linear infinite;
  animation-delay: 4s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(64):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(65) {
  width: 3px;
  height: 3px;
  left: 99px;
  top: 225px;
  animation: twinkle65 13s linear infinite;
  animation-delay: 9s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(65):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(66) {
  width: 2px;
  height: 2px;
  left: 346px;
  top: 126px;
  animation: twinkle66 9s linear infinite;
  animation-delay: 13s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(66):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(67) {
  width: 3px;
  height: 3px;
  left: 164px;
  top: 338px;
  animation: twinkle67 12s linear infinite;
  animation-delay: 17s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(67):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(68) {
  width: 1px;
  height: 1px;
  left: 19px;
  top: 347px;
  animation: twinkle68 12s linear infinite;
  animation-delay: 4s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(68):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(69) {
  width: 3px;
  height: 3px;
  left: 85px;
  top: 213px;
  animation: twinkle69 12s linear infinite;
  animation-delay: 7s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(69):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(70) {
  width: 2px;
  height: 2px;
  left: 270px;
  top: 315px;
  animation: twinkle70 10s linear infinite;
  animation-delay: 18s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(70):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(71) {
  width: 3px;
  height: 3px;
  left: 180px;
  top: 38px;
  animation: twinkle71 9s linear infinite;
  animation-delay: 10s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(71):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(72) {
  width: 1px;
  height: 1px;
  left: 388px;
  top: 254px;
  animation: twinkle72 10s linear infinite;
  animation-delay: 17s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(72):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(73) {
  width: 1px;
  height: 1px;
  left: 15px;
  top: 99px;
  animation: twinkle73 8s linear infinite;
  animation-delay: 13s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(73):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(74) {
  width: 2px;
  height: 2px;
  left: 154px;
  top: 171px;
  animation: twinkle74 8s linear infinite;
  animation-delay: 5s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(74):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(75) {
  width: 3px;
  height: 3px;
  left: 315px;
  top: 180px;
  animation: twinkle75 6s linear infinite;
  animation-delay: 15s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(75):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(76) {
  width: 2px;
  height: 2px;
  left: 115px;
  top: 341px;
  animation: twinkle76 11s linear infinite;
  animation-delay: 14s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(76):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(77) {
  width: 2px;
  height: 2px;
  left: 160px;
  top: 84px;
  animation: twinkle77 10s linear infinite;
  animation-delay: 5s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(77):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(78) {
  width: 2px;
  height: 2px;
  left: 136px;
  top: 111px;
  animation: twinkle78 6s linear infinite;
  animation-delay: 6s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(78):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(79) {
  width: 2px;
  height: 2px;
  left: 367px;
  top: 138px;
  animation: twinkle79 9s linear infinite;
  animation-delay: 18s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(79):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(80) {
  width: 3px;
  height: 3px;
  left: 205px;
  top: 259px;
  animation: twinkle80 8s linear infinite;
  animation-delay: 7s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(80):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(81) {
  width: 2px;
  height: 2px;
  left: 385px;
  top: 136px;
  animation: twinkle81 6s linear infinite;
  animation-delay: 10s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(81):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(82) {
  width: 2px;
  height: 2px;
  left: 227px;
  top: 231px;
  animation: twinkle82 10s linear infinite;
  animation-delay: 5s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(82):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(83) {
  width: 2px;
  height: 2px;
  left: 263px;
  top: 81px;
  animation: twinkle83 11s linear infinite;
  animation-delay: 10s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(83):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(84) {
  width: 3px;
  height: 3px;
  left: 187px;
  top: 135px;
  animation: twinkle84 11s linear infinite;
  animation-delay: 4s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(84):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(85) {
  width: 1px;
  height: 1px;
  left: 210px;
  top: 246px;
  animation: twinkle85 9s linear infinite;
  animation-delay: 18s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(85):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(86) {
  width: 2px;
  height: 2px;
  left: 68px;
  top: 89px;
  animation: twinkle86 13s linear infinite;
  animation-delay: 14s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(86):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(87) {
  width: 3px;
  height: 3px;
  left: 150px;
  top: 332px;
  animation: twinkle87 13s linear infinite;
  animation-delay: 15s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(87):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(88) {
  width: 3px;
  height: 3px;
  left: 245px;
  top: 113px;
  animation: twinkle88 11s linear infinite;
  animation-delay: 10s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(88):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(89) {
  width: 1px;
  height: 1px;
  left: 368px;
  top: 315px;
  animation: twinkle89 9s linear infinite;
  animation-delay: 17s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(89):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(90) {
  width: 1px;
  height: 1px;
  left: 301px;
  top: 334px;
  animation: twinkle90 11s linear infinite;
  animation-delay: 14s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(90):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(91) {
  width: 2px;
  height: 2px;
  left: 167px;
  top: 288px;
  animation: twinkle91 13s linear infinite;
  animation-delay: 9s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(91):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(92) {
  width: 3px;
  height: 3px;
  left: 324px;
  top: 244px;
  animation: twinkle92 11s linear infinite;
  animation-delay: 9s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(92):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(93) {
  width: 1px;
  height: 1px;
  left: 190px;
  top: 84px;
  animation: twinkle93 10s linear infinite;
  animation-delay: 4s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(93):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(94) {
  width: 1px;
  height: 1px;
  left: 171px;
  top: 279px;
  animation: twinkle94 13s linear infinite;
  animation-delay: 11s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(94):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(95) {
  width: 2px;
  height: 2px;
  left: 332px;
  top: 302px;
  animation: twinkle95 11s linear infinite;
  animation-delay: 9s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(95):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(96) {
  width: 3px;
  height: 3px;
  left: 349px;
  top: 186px;
  animation: twinkle96 11s linear infinite;
  animation-delay: 8s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(96):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(97) {
  width: 1px;
  height: 1px;
  left: 180px;
  top: 84px;
  animation: twinkle97 7s linear infinite;
  animation-delay: 5s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(97):before {
  content: "";
  width: 1px;
  height: 1px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(98) {
  width: 3px;
  height: 3px;
  left: 133px;
  top: 34px;
  animation: twinkle98 13s linear infinite;
  animation-delay: 15s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(98):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(99) {
  width: 2px;
  height: 2px;
  left: 386px;
  top: 322px;
  animation: twinkle99 11s linear infinite;
  animation-delay: 9s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(99):before {
  content: "";
  width: 2px;
  height: 2px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(100) {
  width: 3px;
  height: 3px;
  left: 183px;
  top: 220px;
  animation: twinkle100 9s linear infinite;
  animation-delay: 16s;
}
.wrapper .window_group .window_404 .stars .star:nth-of-type(100):before {
  content: "";
  width: 3px;
  height: 3px;
  position: absolute;
  top: 0;
  left: 0;
  background: #fff;
  filter: blur(1px);
}

@keyframes twinkle1 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle2 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle3 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle4 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle5 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle6 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle7 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle8 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle9 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle10 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle11 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle12 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle13 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle14 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle15 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle16 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle17 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle18 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle19 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle20 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle21 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle22 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle23 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle24 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle25 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle26 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle27 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle28 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle29 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle30 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle31 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle32 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle33 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle34 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle35 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle36 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle37 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle38 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle39 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle40 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle41 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle42 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle43 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle44 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle45 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle46 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle47 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle48 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle49 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle50 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle51 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle52 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle53 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle54 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle55 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle56 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle57 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle58 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle59 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle60 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle61 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle62 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle63 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle64 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle65 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle66 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle67 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle68 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle69 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle70 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle71 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle72 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle73 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle74 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle75 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle76 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle77 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle78 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle79 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle80 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle81 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle82 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle83 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle84 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle85 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle86 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle87 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle88 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle89 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle90 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle91 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle92 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle93 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle94 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle95 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle96 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle97 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle98 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle99 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes twinkle100 {
  0% {
    transform: scale(1, 1);
  }
  10% {
    transform: scale(0.3, 0.3);
  }
  20% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(0.5, 0.5);
  }
  40% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(1, 1);
  }
}
@keyframes flyby {
  from {
    left: 0%;
  }
  to {
    left: -100%;
  }
}
@media only screen and (min-width: 1080px) {
  .wrapper .text_group {
    flex: 0 0 30%;
    margin-left: 25%;
    align-items: flex-end;
  }
  .wrapper .window_group {
    flex: 1 0 40%;
    margin-top: 0;
    margin-left: 5%;
  }
}
@media only screen and (max-width: 1079px) {
  .wrapper .text_group {
    flex: 0 0 100%;
    margin: 0;
    align-items: center;
  }
  .wrapper .text_group .text_lost {
    width: 100%;
    padding: 0 22px;
    font-size: 1.7em;
    line-height: 35px;
  }
  .wrapper .window_group {
    flex: 0 0 100%;
  }
  .wrapper .window_group .window_404 {
    margin-left: 50%;
    transform: translateX(-50%);
    margin-top: 20px;
  }
}

    </style>
  
</head>
<body>
<div class="wrapper">
<div class="text_group">
  <p class="text_404">404</p>
  <p class="text_lost">Siden du leter etter <br />har forsvunnet i verdensrommet.</p>
</div>
<div class="window_group">
  <div class="window_404">
    <div class="stars"></div>
  </div>
</div>
</div>


<script>
let starContainer = document.querySelector(".stars");

for (let i = 0; i < 100; i++) {
  starContainer.innerHTML += '<div class="star"></div>';
}
</script>

</body>
</html>



<?php
die();
?>