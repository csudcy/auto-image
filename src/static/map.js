
document.addEventListener('DOMContentLoaded', function() {
  let map = L.map('map').setView([51, 0], 2);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);

  let markers = L.markerClusterGroup();
  map.addLayer(markers);

  function onEachFeature(feature, layer) {
    if (feature.properties) {
      const props = feature.properties;

      let text;
      if (props.location && props.time_taken_text) {
        text = `${props.location}<br/>${props.time_taken_text}`;
      } else if (props.location) {
        text = props.location;
      } else if (props.time_taken_text) {
        text = props.time_taken_text;
      } else {
        text = props.file_id;
      }

      let link;
      if (props.group_index) {
        link = `/group/${props.group_index}`;
      } else {
        link = `/result/${props.file_id}`;
      }
      layer.bindPopup(`
        <p>
          <a href="${link}" target="_blank">
            <div class="image-thumbnail">
              <img src="/image/${props.file_id}"/>
            </div>
            ${text}
          </a>
        </p>`);
    }
  }

  fetch("/api/map/points")
    .then((response) => response.json())
    .then((response) => {
      L.geoJSON(response.points, {
        onEachFeature: onEachFeature
      }).addTo(markers);
    });
});
