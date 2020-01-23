/*jshint esversion: 6 */

const STATUS_INITIAL = 0;
const STATUS_TO_FETCH = 1;
const STATUS_FETCHING = 2;
const STATUS_FETCHED = 3;
const STATUS_ERROR = 4;

const Vue = window.Vue;

function clog(message) {
  window.console.log(message);
}

$(() => {
  let app = new Vue({
    el: '#text-viewer',
    data: {
      texts: [],
      blocks: [],
    },
    mounted() {
      let self = this;
      $.getJSON('/api/texts/?group=declaration').done(res => {
        Vue.set(self, 'texts', res.data);
        clog(res);
        self.init_blocks();
      });
    },
    watch: {
      blocks: {
        handler: function() {
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
    methods: {
      on_view_changed: function(block, view) {
        view.status = STATUS_FETCHING;
        let self = this;
        $.getJSON('/api/texts/'+block.text.id+'/'+view.type+'/whole/whole/')
        .done(res => {
          view.chunk = res.data.attributes.chunk;
          view.status = STATUS_FETCHED;
          self.update_query_string();
        })
        .fail(res => {
          view.status = STATUS_ERROR;
        });
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
        // original copy
        let self = this;
        let query_string_blocks = window.location.href.replace(/.*blocks=([^#&]+).*/, '$1');
        if (query_string_blocks != window.location) {
          for (let block_info of query_string_blocks.split(';')) {
            if (block_info) {
              let parts = block_info.split(':');
              this.blocks.push({
                text: self.get_text_from_id_or_siglum(parts[0]),
                views: parts[1].split(',').map(
                  view_type => ({type: view_type, chunk: null, status: STATUS_TO_FETCH})
                ),
                comparative: false,
              });
            }
          }
        }
        if (this.blocks.length < 1) {
          this.blocks.push({
            text: self.get_default_text(),
            views: [{type: 'transcription', chunk: null, status: STATUS_TO_FETCH}],
            comparative: false,
          });
        }
        if (this.blocks.length < 2) {
          this.blocks.push({
            text: null,
            views: [{type: 'transcription', chunk: 'placeholder', status: STATUS_FETCHED}],
            comparative: false,
          });
        }

        Vue.nextTick(function() {
          $('.off-canvas-absolute:not(.foundation-initialised)').each(function() {
            $(this).addClass('foundation-initialised');
            new window.Foundation.OffCanvas($(this));
          });

        });
      },
      get_text_from_id_or_siglum: function (id_or_siglum) {
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
      on_change_text: function(block, text) {
        block.text = text;
        for (let view of block.views) {
          view.status = STATUS_TO_FETCH;
        }
      }
    }
  });
});

