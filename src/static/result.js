document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.centreable').forEach(centreable => {
      const img = centreable.querySelector('img');
      const imageId = img.dataset.id;
      const targetCropImg = document.querySelector(`.centreable-cropped[data-id="${imageId}"]`);
      const marker = document.createElement('div');
      marker.className = 'marker';
      centreable.appendChild(marker);

      const updateMarkerFromData = () => {
          // Calculate the scale ratio
          const rect = img.getBoundingClientRect();
          const scaleX = rect.width / img.naturalWidth;
          const scaleY = rect.height / img.naturalHeight;

          // Set position relative to the displayed size
          marker.style.left = (img.offsetLeft + parseFloat(img.dataset.centreX) * scaleX) + "px";
          marker.style.top = (img.offsetTop + parseFloat(img.dataset.centreY) * scaleY) + "px";
      };

      // Click logic: Update marker AND data attributes
      img.addEventListener('click', async function(e) {
          // Click position in current display pixels
          const rect = img.getBoundingClientRect();
          const clickX = e.clientX - rect.left;
          const clickY = e.clientY - rect.top;

          // Convert back to "Natural" pixels for storage
          const newNatX = Math.round(clickX * (img.naturalWidth / rect.width));
          const newNatY = Math.round(clickY * (img.naturalHeight / rect.height));

          // Update Data Attributes & marker
          img.setAttribute('data-centre-x', newNatX);
          img.setAttribute('data-centre-y', newNatY);
          updateMarkerFromData();

          // Call the API
          targetCropImg.src = '';
          try {
              const response = await fetch(`/api/result/centre/${imageId}`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ x: newNatX, y: newNatY })
              });
              if (response.ok) {
                  // Assuming the API returns the image as a blob
                  const blob = await response.blob();
                  targetCropImg.src = URL.createObjectURL(blob);
              }
          } catch (error) {
              console.error("API Error:", error);
          }
      });

      // Update marker position
      img.onload = updateMarkerFromData;
      window.addEventListener('resize', updateMarkerFromData);
  });
});
