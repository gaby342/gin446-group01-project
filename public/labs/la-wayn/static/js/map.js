(() => {
  const map = L.map('map', {scrollWheelZoom:false}).setView([33.8938,35.5018], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19, attribution:'© OpenStreetMap contributors'}).addTo(map);
  let pin;
  const lat = document.querySelector('#lat'), lon = document.querySelector('#lon'), label = document.querySelector('#location-label');
  function setPin(point) {
    lat.value = point.lat.toFixed(6); lon.value = point.lng.toFixed(6);
    if (pin) pin.setLatLng(point); else pin = L.marker(point,{draggable:true}).addTo(map).on('dragend',e=>setPin(e.target.getLatLng()));
    label.textContent = `${lat.value}, ${lon.value}`;
  }
  map.on('click',e=>setPin(e.latlng));
  const fallback = L.latLng(33.8938,35.5018); setPin(fallback);
  document.querySelector('#locate').addEventListener('click',()=>{
    if (!navigator.geolocation) { label.textContent='Location is unavailable; click the map instead.'; return; }
    label.textContent='Finding your location…';
    navigator.geolocation.getCurrentPosition(pos=>{const p=L.latLng(pos.coords.latitude,pos.coords.longitude);map.setView(p,14);setPin(p);},()=>{label.textContent='Could not access location; click the map instead.';},{timeout:8000});
  });
  document.querySelector('#search-form').addEventListener('submit',async e=>{
    e.preventDefault(); const form=e.currentTarget, button=document.querySelector('#search-button'), error=document.querySelector('#search-error');
    button.disabled=true;button.innerHTML='Finding nearby spots…';error.textContent='';
    const body=Object.fromEntries(new FormData(form)); body.cuisines=[...form.querySelectorAll('[name=cuisines]:checked')].map(x=>x.value);
    const now=new Date(); body.local_weekday=now.getDay(); body.local_minute=now.getHours()*60+now.getMinutes();
    for(const key of ['open_now','vegetarian','halal']) body[key]=form.querySelector(`[name=${key}]`).checked;
    try {const response=await fetch(form.action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const result=await response.json();if(!response.ok)throw Error(result.error||'Could not search.');location.href=result.redirect;}
    catch(err){error.textContent=err.message;button.disabled=false;button.innerHTML='Find the deck <span>↗</span>';}
  });
})();
