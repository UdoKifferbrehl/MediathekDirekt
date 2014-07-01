var data = [];
$.getJSON("good.json", function(jsondata)
{
  data = data.concat(jsondata);
  document.getElementById("message").innerHTML="Suche nach Sendung: (nur letzte Woche, lade noch weiter...)";
  search(document.getElementById("needle").value);
});
$.getJSON("medium.json", function(jsondata)
{
  data = data.concat(jsondata);
  document.getElementById("message").innerHTML="Suche nach Sendung:";
  search(document.getElementById("needle").value);
});

function printSendung(s, classname)
{
  link = s[7].substr(s[7].lastIndexOf('.') + 1);
  document.getElementById("results").innerHTML+="<div class='"+classname+"'><span class='r1'><a href='"+s[7]+"'>"+s[1]+" "+s[2]+"</a> - <a href='"+s[8]+"' style='font-size:80%'>web</a></span><br><span class='r2'>"+s[0]+" "+s[3]+" "+s[4]+" "+s[5]+" "+link+" "+s[9]+"</span><br><span class='r3'>"+s[6]+"</a></div>";
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
function tipp(s)
{
  document.getElementById("needle").value=s;
  search(s);
}
function more() { $(".resmore").show(); $("#mehr").hide();}
