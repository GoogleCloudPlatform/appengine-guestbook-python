var submit = document.getElementById("gbsubmit");
var name = document.getElementById("gbname");
var form = document.getElementById("gbform");
var row = document.getElementById("gbrow");
var rows = [];
var table = row.parentNode;
function updateGuestbook() {
  var url = "?guestbook_name="+encodeURIComponent(gbname.value);
  submit.elements.guestbook_name.value = gbname.value;
  history.pushState(null, "", url);
  // Remove old rows.
  rows.forEach(r=>r.parentNode.removeChild(r));
  rows=[];
  fetch("/guestbook" + url, {credentials: "include"}).then(r=>r.json()).then(j=>{
    j.forEach(m=>{
      var elem = table.insertBefore(row.cloneNode(true), table.firstChild);
      rows.push(elem);
      // Note this is an XSS.
      elem.getElementsByTagName("blockquote")[0].innerHTML=m.content;
    });
  }).catch(e=>{
    alert("Error loading guestbook comments");
  });
  return false;
}
gbform.onsubmit = window.onload = updateGuestbook;
