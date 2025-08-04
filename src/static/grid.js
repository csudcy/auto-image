document.addEventListener('DOMContentLoaded', () => {
  const CONTENT_PANEL = document.querySelector('.content-panel');
  const GRID_ITEMS = document.querySelectorAll('.content-panel .grid');
  const ITEM_COUNT = GRID_ITEMS.length;
  const ITEM_PADDING = 6;
  const MAX_COLUMNS = 20;
  var lastItemSize = 1;

  function updateItemSize() {
    const RECT = getComputedStyle(CONTENT_PANEL);
    const WIDTH = parseFloat(RECT.width);
    const HEIGHT = parseFloat(RECT.height);

    // Find the optimal item size
    var itemSize = 0;
    for (var columns=MAX_COLUMNS; columns>0; columns--) {
      const ROWS = Math.ceil(ITEM_COUNT / columns);
      const ITEM_WIDTH = Math.floor(WIDTH / columns);
      const ITEM_HEIGHT = Math.floor(HEIGHT / ROWS);
      const ITEM_SIZE = Math.min(ITEM_WIDTH, ITEM_HEIGHT);
      if (ITEM_SIZE > itemSize) {
        itemSize = ITEM_SIZE;
      }
    }

    // If it's different from current size, update all items
    if (lastItemSize !== itemSize) {
      const ITEM_PX = `${itemSize - ITEM_PADDING}px`;
      GRID_ITEMS.forEach((item) => {
        item.style.width = ITEM_PX;
        item.style.height = ITEM_PX;
      });
      lastItemSize = itemSize;
    }
  }

  window.addEventListener('resize', updateItemSize);
  updateItemSize();
});
