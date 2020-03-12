/*jshint esversion: 6 */

// Content loading statuses
const STATUS_INITIAL = 0
const STATUS_TO_FETCH = 1
const STATUS_FETCHING = 2
const STATUS_FETCHED = 3
const STATUS_ERROR = 4

const Vue = window.Vue
const L = window.L
// These are the dimensions of the image in Archetype.
// We use a bigger version of that image for COTR site.
// Hence the need for ad-hoc scaling.
const ARCHETYPE_IMAGE_DIMENSIONS = [3212, 4392]

// magic number... see leaflet-iiif annotation example
// https://bl.ocks.org/mejackreed/raw/2724146adfe91233c74120b9056fba06/
// https://bl.ocks.org/mejackreed/raw/2724146adfe91233c74120b9056fba06/app.js
// https://github.com/mejackreed/Leaflet-IIIF/blob/master/leaflet-iiif.js#L45
const LEAFLET_ZOOM_TRANFORM = 3

const TYPES_LABEL = {
  transcription: 'Latin',
  translation: 'English',
  histogram: 'Histogram'
}

const PRESELECTED_TEXT_SIGLA = ['V1']

const DEFAULT_RESULT_TYPE = window.DEBUG ? 'regions' : 'sentences'
// const DEFAULT_RESULT_TYPE = 'sentences';

const SENTENCE_NUMBER_MAX = 27

// maximum number of distinct readings per region (in Declaration)
// actual maximum is 17 but we cap it to 10
// => - all values above look like 10
// => + 2 or 3 distinct readings are more distinct visually
const DISTINCT_READINGS_MAX = 10

function clog(message) {
  window.console.log(message)
}

$(() => {
  let app = new Vue({
    el: '#text-search',
    data: {
      status: STATUS_TO_FETCH,
      facets: {
        result_type: DEFAULT_RESULT_TYPE,
        sentence_number: 1,
        encoding_type: 'transcription',
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
        texts: []
      },
      blocks: [],
      response: {},
      selected_region: null
    },
    mounted() {
      let self = this
      $.getJSON('/api/texts/?group=declaration').done(res => {
        Vue.set(self.facets, 'texts', res.data)
        // clog(res);

        // add direct references to parent texts
        // for convenience in the template.
        for (let text of this.facets.texts) {
          text.parent = this.get_text_from_id_or_siglum(text.attributes.group)
        }

        for (let siglum of PRESELECTED_TEXT_SIGLA) {
          let text = self.get_text_from_id_or_siglum(siglum)
          text.selected = true
          self.on_tick_text(text, true)
        }

        // self.init_blocks();
        self.fetch_results()
      })
    },
    computed: {
      text_types: function() {
        return [
          // {label: 'Work', type: 'work'},
          { label: 'Versions', type: 'version' },
          { label: 'Manuscripts', type: 'manuscript' }
        ]
      },
      sentence_number_max: function() {
        return SENTENCE_NUMBER_MAX
      },
      debug_mode: function() {
        return window.DEBUG
      }
    },
    watch: {
      'facets.deprecated': {
        handler: function() {
          // Something has changed in a block or view,
          // fetch view content if needed.
          this.fetch_results()
        },
        deep: true
      },
      'facets.sentence_number': function() {
        this.fetch_results()
      },
      'facets.result_type': function() {
        this.fetch_results()
      },
      'facets.encoding_type': function() {
        this.fetch_results()
      }
    },
    filters: {
      view_type_label: function(value) {
        return TYPES_LABEL[value]
      }
    },
    methods: {
      on_tick_text: function(text, silent) {
        let selected = text.selected

        if (text.type == 'version') {
          // select all members accordingly
          for (let member of this.facets.texts) {
            if (member.parent === text) {
              member.selected = selected
            }
          }
        }
        if (text.type == 'manuscript') {
          // deselect parent of member is unselected
          if (!selected) {
            text.parent.selected = selected
          }
        }

        if (!silent) this.fetch_results()
      },
      fetch_results: function(block, view) {
        if (this.status == STATUS_FETCHING) return

        // hide readings section
        _on_rect_popupclose(null)

        this.status = STATUS_FETCHING
        let self = this

        let text_ids = []
        for (let t of self.facets.texts) {
          if (t.selected) {
            text_ids.push(t.id)
          }
        }

        $.getJSON('/api/texts/search/' + self.facets.result_type + '/', {
          texts: text_ids.join(','),
          et: self.facets.encoding_type,
          sn: self.facets.sentence_number
        })
          .done(res => {
            // clog(res);
            self.status = STATUS_FETCHED
            Vue.set(self, 'response', res)
            // self.update_query_string();

            Vue.nextTick(function() {
              init_leaflet(res)
            })
          })
          .fail(res => {
            self.status = STATUS_ERROR
          })
      },

      get_text_from_id_or_siglum: function(id_or_siglum) {
        id_or_siglum += ''
        for (let text of this.facets.texts) {
          if (
            text.id == id_or_siglum ||
            text.attributes.siglum.toLowerCase() == id_or_siglum.toLowerCase()
          ) {
            return text
          }
        }
        return null
      },

      get_default_text: function() {
        return this.get_text_from_id_or_siglum('O')
      },

      move_sentence_number: function(increment) {
        let ret = (parseInt(this.facets.sentence_number) || 1) + increment
        if (ret < 1) ret = 1
        if (ret > this.sentence_number_max) ret = this.sentence_number_max
        this.facets.sentence_number = ret
      }
    }
  })

  function init_leaflet(response) {
    $('[data-leaflet-iiif]').each(function() {
      if (!$(this).hasClass('ctrs-initialised')) {
        $(this).addClass('ctrs-initialised')

        let map = L.map(this, {
          center: [0, 0],
          crs: L.CRS.Simple,
          zoom: 0
        })
        window.map = map
        map.annotation_loaded = false

        let image_layer = L.tileLayer
          .iiif(this.getAttribute('data-leaflet-iiif'))
          .addTo(map)
        window.image_layer = image_layer

        // Unfortunately I couldn't find an event for json loaded
        // https://github.com/mejackreed/Leaflet-IIIF/blob/master/leaflet-iiif.js#L73
        // so we are going through this frequent tile-related event instead
        // but make sure we execute only once.
        image_layer.on('load', function() {
          if (this.annotation_loaded) return
          load_annotations(this, response)
          // map.setZoom(0);
          this.annotation_loaded = true
        })
      } else {
        for (let rect of window.annotations) {
          // TODO: update color instead of removing and adding everything again
          window.map.removeLayer(rect)
        }
        load_annotations(window.image_layer, response)
      }
    })
  }

  function load_annotations(image_layer, response) {
    // iiif-image metadata is loaded, now we draw all the annotations
    // TODO: avoid using _ property
    let ret = response.data[0].annotations

    let map = image_layer._map

    // make the regions accessible by their keys.
    // TODO: check that this code works on mobile/older browsers.
    // regions becomes an array with keys... convenient but unorthodox.
    let regions = response.data[0].regions
    window.regions = regions
    for (let i = regions.length - 1; i > -1; i--) {
      regions[regions[i].key] = regions[i]
    }

    // we draw all the rectangles.
    // replace each pair of coordinates in an.rects
    // with a reference to the new rectangle.
    window.annotations = []

    for (let [key, an] of Object.entries(ret)) {
      an.key = key
      for (let i = 0; i < an.rects.length; i++) {
        let style = _get_annotation_style(an)
        if (style) {
          let rect = L.rectangle(ps2cs(image_layer, an.rects[i]), style).addTo(
            map
          )
          rect.annotation = an
          rect.on('mousedown', _on_rect_mousedown)
          rect.on('mouseover', _on_rect_mouseover)
          rect.on('mouseout', _on_rect_mouseleave)
          rect.on('popupclose', _on_rect_popupclose)
          an.rects[i] = rect
          window.annotations.push(rect)
        }
      }
    }

    return ret
  }

  function _on_rect_mousedown(e) {
    _on_rect_mouseover(e)

    Vue.nextTick(function() {
      const popupContent = document
        .getElementById('heatmap-tooltip')
        .cloneNode(true)
      popupContent.id = 'leaflet-heatmap-tooltip'

      e.target
        .bindPopup(popupContent, {
          class: 'custom-tooltip',
          maxWidth: '1000'
        })
        .addTo(window.map)
    })
  }

  function _on_rect_mouseover(e) {
    let region_key = e.target.annotation.key
    app.selected_region = window.regions[region_key]
  }

  function _on_rect_mouseleave(e) {
    const popup = e.target.getPopup()
    if (popup === undefined || !popup.isOpen()) {
      app.selected_region = null
    }
  }

  function _on_rect_popupclose(e) {
    app.selected_region = null
  }

  function _get_annotation_style(annotation) {
    let ret = {
      color: '#ff0000',
      weight: 1,
      fillOpacity: 0.3
    }

    let region = window.regions[annotation.key]
    if (!region) {
      clog(
        'WARNING: annotation key ' + annotation.key + ' not found in regions'
      )
      if (window.DEBUG) {
        ret.color = '#0000ff'
      } else {
        ret.fillOpacity = 0
        ret.weight = 0
      }
    } else {
      let freq = Object.keys(region.readings).length
      freq = Math.min(freq, DISTINCT_READINGS_MAX)

      if (freq < 2) {
        ret.fillOpacity = 0
        ret.weight = 0
        ret = null
      } else {
        ret.color =
          'rgb(255, ' +
          (1 - (freq - 2) / (DISTINCT_READINGS_MAX - 2)) * 255 +
          ', 0)'
        // clog(freq);
        // clog(ret);
      }
    }

    return ret
  }

  // returns coordinates from [x, y] point extracted from archetype geo_json
  function p2c(image_layer, p) {
    let map = image_layer._map
    return map.unproject(
      L.point(
        (p[0] / ARCHETYPE_IMAGE_DIMENSIONS[0]) * image_layer.x,
        image_layer.y - (p[1] / ARCHETYPE_IMAGE_DIMENSIONS[1]) * image_layer.y
      ),
      LEAFLET_ZOOM_TRANFORM
    )
  }
  // returns coordinate pair from [[x0, y0], [x1, y1]]
  function ps2cs(image_layer, b) {
    return [p2c(image_layer, b[0]), p2c(image_layer, b[1])]
  }
})
