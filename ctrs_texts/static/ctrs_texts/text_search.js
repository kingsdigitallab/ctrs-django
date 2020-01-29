/*jshint esversion: 6 */

// Content loading statuses
const STATUS_INITIAL = 0;
const STATUS_TO_FETCH = 1;
const STATUS_FETCHING = 2;
const STATUS_FETCHED = 3;
const STATUS_ERROR = 4;

const Vue = window.Vue;

const TYPES_LABEL = {
  transcription: 'Latin',
  translation: 'English',
  histogram: 'Histogram',
};

const PRESELECTED_TEXT_SIGLA = ['O', 'JH'];

function clog(message) {
  window.console.log(message);
}

$(() => {
  let app = new Vue({
    el: '#text-search',
    data: {
      status: STATUS_TO_FETCH,
      facets: {
        result_type: 'sentences',
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
          self.update_query_string();
        })
        .fail(res => {
          self.status = STATUS_ERROR;
        });
      },

      update_query_string: function() {
        return;
        // update query string with current state of viewer
        // e.g. ?blocks=506:transcription,transcription;495:transcription
        var self = this;
        let qs = 'blocks=' + self.blocks.map(
          b => b.text ? b.text.id + ':' + (b.views.map(v => v.type)).join(','): ''
        ).join(';');
        qs = window.location.href.replace(/^([^?]+)([^#]+)(.*)$/, '$1?'+qs+'$3');
        history.pushState(null, '', qs);
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
});

