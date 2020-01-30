/*jshint esversion: 6 */

// Content loading statuses
const STATUS_INITIAL = 0;
const STATUS_TO_FETCH = 1;
const STATUS_FETCHING = 2;
const STATUS_FETCHED = 3;
const STATUS_ERROR = 4;

const Vue = window.Vue;
const L = window.L;
const ARCHETYPE_IMAGE_DIMENSIONS = [3212, 4392]

// magic number... see leaflet-iiif annotation example
// https://bl.ocks.org/mejackreed/raw/2724146adfe91233c74120b9056fba06/
// https://bl.ocks.org/mejackreed/raw/2724146adfe91233c74120b9056fba06/app.js
// https://github.com/mejackreed/Leaflet-IIIF/blob/master/leaflet-iiif.js#L45
const LEAFLET_ZOOM_TRANFORM = 3;

const TYPES_LABEL = {
  transcription: 'Latin',
  translation: 'English',
  histogram: 'Histogram',
};

const PRESELECTED_TEXT_SIGLA = ['O', 'JH'];

const DEFAULT_RESULT_TYPE = 'regions';

function clog(message) {
  window.console.log(message);
}

$(() => {
  let app = new Vue({
    el: '#text-search',
    data: {
      status: STATUS_TO_FETCH,
      facets: {
        result_type: DEFAULT_RESULT_TYPE,
        /*
        List of all available texts. Exactly as returned by /api/texts/.

        texts: [{
          id: <TEXT_ID>,
          type: 'manuscript'|'version'|'work',
          list_heading: 'manuscript'|'version'|'work',
          attributes: {
            siglum: ,
            name: ,
            group: <ID_OF_A_TEXT>,
          }
        }, [...]]
        */
        texts: [],
      },
      blocks: [],
      response: {},
    },
    mounted() {
      let self = this;
      $.getJSON('/api/texts/?group=declaration').done(res => {
        Vue.set(self.facets, 'texts', res.data);
        clog(res);

        for (let siglum of PRESELECTED_TEXT_SIGLA) {
            self.get_text_from_id_or_siglum(siglum).selected = true;
        }

        // self.init_blocks();
      });
    },
    computed: {
      text_types: function() {
        return [
          // {label: 'Work', type: 'work'},
          {label: 'Versions', type: 'version'},
          {label: 'Manuscripts', type: 'manuscript'},
        ];
      },
    },
    watch: {
      facets: {
        handler: function() {
          // Something has changed in a block or view,
          // fetch view content if needed.
          this.fetch_results();
        },
        deep: true
      }
    },
    filters: {
      view_type_label: function(value) {
        return TYPES_LABEL[value];
      }
    },
    methods: {
      fetch_results: function(block, view) {
        if (this.status == STATUS_FETCHING) return;
        this.status = STATUS_FETCHING;
        let self = this;

        let text_ids = [];
        for (let t of self.facets.texts) {
          if (t.selected) {
            text_ids.push(t.id);
          }
        }

        $.getJSON(
          '/api/texts/search/'+self.facets.result_type+'/',
          {'texts': text_ids.join(',')}
        )
        .done(res => {
          clog(res);
          self.status = STATUS_FETCHED;
          Vue.set(self, 'response', res);
          // self.update_query_string();

          Vue.nextTick(function() {
            init_leaflet(res);
          });
        })
        .fail(res => {
          self.status = STATUS_ERROR;
        });
      },

      get_text_from_id_or_siglum: function (id_or_siglum) {
        for (let text of this.facets.texts) {
          if (
            text.id == id_or_siglum ||
            text.attributes.siglum.toLowerCase() == id_or_siglum.toLowerCase()
          ) {
            return text;
          }
        }
        return null;
      },

      get_default_text: function () {
        return this.get_text_from_id_or_siglum('O');
      },

    }
  });


  function init_leaflet(response) {
    $('[data-leaflet-iiif]').each(function() {
      if (!$(this).hasClass('ctrs-initialised')) {
        window.rectangles = [];

        $(this).addClass('ctrs-initialised');

        let map = L.map(this, {
          center: [0, 0],
          crs: L.CRS.Simple,
          zoom: 0
        });
        window.map = map;
        map.annotation_loaded = false;

        let image_layer = L.tileLayer.iiif(
          this.getAttribute('data-leaflet-iiif')
        ).addTo(map);
        window.image_layer = image_layer;

        // Unfortuantely I couldn't find an event for json loaded
        // https://github.com/mejackreed/Leaflet-IIIF/blob/master/leaflet-iiif.js#L73
        // so we are going through this frequent tile-related event instead
        // but make sure we execute only once.
        image_layer.on('load', function() {
          if (this.annotation_loaded) return;
          load_annotations(this, response);
          this.annotation_loaded = true;
        });
      } else {
        for (let rect of window.rectangles) {
          // TODO: update color instead of removing and adding everything again
          window.map.removeLayer(rect);
        }
        window.rectangles = [];
        load_annotations(window.image_layer, response);
      }
    });
  }

  function load_annotations(image_layer, response) {
    // iiif-image metadata is loaded, now we draw all the annotations
    // TODO: avoid using _ property
    let map = image_layer._map;

    for (let an of response.data[0].annotations) {
      let coordinates = an.geo_json.geometry.coordinates[0];
      let bounds = ps2cs(image_layer, [coordinates[0], coordinates[2]]);
      let rect = L.rectangle(bounds, {color: "#ff0000", weight: 1}).addTo(map);
      window.rectangles.push(rect);
      // break;
    }
  }

  // returns coordinates from [x, y] point extracted from archetype geo_json
  function p2c(image_layer, p) {
    let map = image_layer._map;
    return map.unproject(
      L.point(
        p[0] / ARCHETYPE_IMAGE_DIMENSIONS[0] * image_layer.x,
        image_layer.y - (p[1] / ARCHETYPE_IMAGE_DIMENSIONS[1] * image_layer.y)
      ),
      LEAFLET_ZOOM_TRANFORM
    );
  }
  // returns coordinate pair from [[x0, y0], [x1, y1]]
  function ps2cs(image_layer, b) {
    return [p2c(image_layer, b[0]), p2c(image_layer, b[1])];
  }

});

