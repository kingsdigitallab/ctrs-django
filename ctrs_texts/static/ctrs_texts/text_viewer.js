/*jshint esversion: 6 */

// Content loading statuses
const STATUS_INITIAL = 0;
const STATUS_TO_FETCH = 1;
const STATUS_FETCHING = 2;
const STATUS_FETCHED = 3;
const STATUS_ERROR = 4;

// are the w-regions highlighted by default
const DISPLAY_WREGIONS_DEFAULT = true;

const Vue = window.Vue;

const TYPES_LABEL = {
  transcription: 'Latin',
  translation: 'English translation',
//  histogram: 'Histogram',
};

function clog(message) {
  window.console.log(message);
}

$(() => {
  let app = new Vue({
    el: '#text-viewer',
    data: {
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
      /*
      List of all UI Blocks and their Views.
      A block is a UI unit for a particular text.
      A view is a UI unit for a view of that text.

      blocks: [{
        text: <REFERENCE TO this.texts[i]>,
        comparative: <BOOLEAN>,
        views: [
          status: STATUS_XXX,
          type: 'transcription'|'translation'|'histogram'|...
          chunk: <HTML content for this view type of the text>
        ]
      }, [...]
      ]
      */
      blocks: [],
    },
    mounted() {
      let self = this;
      $.getJSON('/api/texts/?group=declaration').done(res => {
        Vue.set(self, 'texts', res.data);

        // add direct references to parent texts
        // for convenience in the template.
        for (let text of this.texts) {
            text.parent = this.get_text_from_id_or_siglum(text.attributes.group);
        }

        self.init_blocks();
      });
    },
    computed: {
      view_types: function() {
        return TYPES_LABEL;
      },
      text_types: function() {
        return [
          {label: 'Work', type: 'work'},
          {label: 'Versions', type: 'version'},
          {label: 'Manuscripts', type: 'manuscript'},
        ];
      },
    },
    watch: {
      blocks: {
        handler: function() {
          // Something has changed in a block or view,
          // fetch view content if needed.
          let qs = '';
          for (let block of this.blocks) {
            for (let view of block.views) {
              if (view.status === STATUS_TO_FETCH) {
                this.on_view_changed(block, view);
              }
            }
          }
        },
        deep: true
      }
    },
    filters: {
      view_type_label: function(value) {
        return TYPES_LABEL[value];
      },
    },
    methods: {
      change_view_type: function(block, view, view_type) {
        view.type = view_type;
        this.on_view_changed(block, view);
      },

      toggle_view_display(block, view, display_type) {
        // toggle a display setting for this view
        // all display setttings are prefixed with display_
        let display_key = 'display_'+display_type;
        let v = view[display_key];
        Vue.set(view, display_key, !v);
      },

      on_view_changed: function(block, view) {
        // a view needs its content to be fetched
        view.status = STATUS_FETCHING;
        let self = this;
        $.getJSON('/api/texts/'+block.text.id+'/'+view.type+'/whole/whole/')
        .done(res => {
          view.chunk = res.data.attributes.chunk;
          view.status = STATUS_FETCHED;
          self.update_query_string();

          // add javascript interactions to the text chunk
          Vue.nextTick(function() {
            self._after_chunk_loaded(block, view);
          });
        })
        .fail(res => {
          view.status = STATUS_ERROR;
        });
      },

      on_change_text: function(block, text) {
        // change the text of a block
        // according to the user selection in the UI
        block.text = text;
        for (let view of block.views) {
          // this will trigger a request for content
          view.status = STATUS_TO_FETCH;
        }
      },

      update_query_string: function() {
        // update query string with current state of viewer
        // e.g. ?blocks=506:transcription,transcription;495:transcription
        var self = this;
        let qs = 'blocks=' + self.blocks.map(
          b => b.text ? b.text.id + ':' + (b.views.map(v => v.type)).join(','): ''
        ).join(';');
        qs = window.location.href.replace(/^([^?]+)([^#]+)(.*)$/, '$1?'+qs+'$3');
        history.pushState(null, '', qs);
      },

      init_blocks: function () {
        let self = this;
        // Create blocks from the 'blocks' param in the query strings
        // e.g. ?blocks=506:transcription,transcription;495:transcription
        let query_string_blocks = window.location.href.replace(/.*blocks=([^#&]+).*/, '$1');
        if (query_string_blocks != window.location) {
          for (let block_info of query_string_blocks.split(';')) {
            if (block_info) {
              let parts = block_info.split(':');
              this.blocks.push({
                text: self.get_text_from_id_or_siglum(parts[0]),
                views: parts[1].split(',').map(
                  (view_type) => self._get_new_view_data(view_type)
                ),
                comparative: false,
              });
            }
          }
        }
        // Default blocks, if needed
        if (this.blocks.length < 1) {
          // block for the 'original copy'
          this.blocks.push({
            text: self.get_default_text(),
            views: [self._get_new_view_data()],
            comparative: false,
          });
        }
        if (this.blocks.length < 2) {
          // placeholder block
          this.blocks.push({
            text: null,
            views: [self._get_new_view_data(
              'transcription', 'placeholder', STATUS_FETCHED
            )],
            comparative: false,
          });
        }

        Vue.nextTick(function() {
          // Fundation JS re-initialisation
          $('.off-canvas-absolute:not(.foundation-initialised)').each(function() {
            $(this).addClass('foundation-initialised');
            new window.Foundation.OffCanvas($(this));
          });
        });
      },

      get_text_from_id_or_siglum: function (id_or_siglum) {
        // Gotcha: some texts share the same siglum, e.g. PA in v5 and v6!
        //
        id_or_siglum += '';
        for (let text of this.texts) {
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

      _get_new_view_data: function(view_type, chunk, status) {
        return {
          type: view_type || 'transcription',
          chunk: chunk || null,
          status: (status === undefined) ? STATUS_TO_FETCH : status,
          display_wregions: DISPLAY_WREGIONS_DEFAULT
        };
      },

      _after_chunk_loaded(block, view) {
        // when the user clicks a variant/reading in a region
        // we load the text of that variant in the other block/pane
        let self = this;
        $('.variants').not('.clickable').addClass('clickable').on('click', '.variant', function() {
          let text_id = this.getAttribute('data-tid');
          // find('.ms').first().text();
          let text = self.get_text_from_id_or_siglum(text_id);
          if (text) {
            for (let other_block of self.blocks) {
              if (other_block != block) {
                self.on_change_text(other_block, text);
              }
            }
          }
        });
      },

    }
  });
});

