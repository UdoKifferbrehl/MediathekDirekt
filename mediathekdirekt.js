/*
Copyright 2014, martin776
Copyright 2014, Markus Koschany

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
*/

var data = [];
$.getJSON("good.json", function(jsondata)
{
  data = data.concat(jsondata);
  search(document.getElementById("needle").value);
});
$.getJSON("medium.json", function(jsondata)
{
  data = data.concat(jsondata);
  document.getElementById("message").innerHTML="";
  search(document.getElementById("needle").value);
});

function printSendung(s, classname)
{
  link = s[7].substr(s[7].lastIndexOf('.') + 1);
  document.getElementById("results").innerHTML+="<div class='"+classname+"'><span class='r1'><a href='"+s[7]+"'>"+s[1]+" "+s[2]+"</a> - <a href='"+s[8]+"' style='font-size:80%'>web</a></span><br><span class='r2'>"+s[0]+" "+s[3]+" "+s[4]+" "+s[5]+" "+link+" </span><br><span class='r3'>"+s[6]+"</a></div>";
}

function search(needle)
{
  document.getElementById("results").innerHTML="";
  $("#mehr").hide();
  var r = 0;
  for(var i = 0; i<data.length && r<30; i++)
  {
    var d = data[i];
    if(d[1].toLowerCase().indexOf(needle.toLowerCase()) >= 0 || d[2].toLowerCase().indexOf(needle.toLowerCase()) >= 0)
    {
      if(r<5) printSendung(d, 'res');
      else { printSendung(d, 'resmore'); $("#mehr").show(); }
      r++;
    }
  }
  if(r==0) {
    document.getElementById("results").innerHTML+="Leider keine Ergebnisse.";
  }
}
/*
function tipp(s)
{
  document.getElementById("needle").value=s;
  search(s);
}*/
function more() { $(".resmore").show(); $("#mehr").hide();}

/* Clear input */

function tog(v){return v ?'addClass':'removeClass';}

$(document).on('input', '.clearinput', function(){
   $(this)[tog(this.value)]('x');
}).on('mousemove', '.x', function( e ){
   $(this)[tog(this.offsetWidth-30 < e.clientX-this.getBoundingClientRect().left)]('onX');
}).on('click', '.onX', function(){
   $(this).removeClass('x onX').val('');
});

