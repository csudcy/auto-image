
document.addEventListener('DOMContentLoaded', function() {
  let map = L.map('map').setView([51, 0], 2);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);

  L.marker([51.5, -0.09]).addTo(map);

  var popup = L.popup();
  function onMapClick(e) {
      popup
          .setLatLng(e.latlng)
          .setContent("You clicked the map at " + e.latlng.toString())
          .openOn(map);
  }
  map.on('click', onMapClick);
});
