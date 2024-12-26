function render_bool(value) {
  return value ? '✅' : '❌';
}

document.addEventListener('DOMContentLoaded', function() {
  console.log('Yo');
  $('#data-table').DataTable({
      ajax: {
          url: '/api/results',
          dataSrc: ''
      },
      columns: [
          {
              data: 'file_id',
              title: 'File',
          },
          // {
          //     data: 'centre',
          //     title: 'Centre',
          // },
          {
              data: 'group_index',
              title: 'Group Index',
          },
          {
              data: 'is_chosen',
              title: 'Chosen',
              render: render_bool,
          },
          {
              data: 'is_recent',
              title: 'Recent?',
              render: render_bool,
          },
          {
              data: 'location',
              title: 'Location',
              render: (location, type, row) => {
                if (row.lat_lon) {
                  return `<a
                      href="http://www.openstreetmap.org/?mlat=${row.lat_lon.lat}&mlon=${row.lat_lon.lon}&zoom=9"
                      target="_blank">
                      ${location}
                    </a>`;
                } else {
                  return location;
                }
              },
          },
          {
              data: 'ocr_coverage',
              title: 'OCR Coverage',
              render: $.fn.dataTable.render.number(null, null, 2, null, null),
          },
          {
              data: 'ocr_text',
              title: 'OCR Text',
              render: $.fn.dataTable.render.text(),
              className: 'limit-text-width',
          },
          // {
          //     data: 'scores',
          //     title: 'Scores',
          // },
          {
              data: 'taken',
              title: 'Taken',
              type: 'date',
              render: $.fn.dataTable.render.datetime(),
          },
          {
              data: 'total',
              title: 'Total',
              render: $.fn.dataTable.render.number(null, null, 2, null, null),
          },
      ],
  });
});
