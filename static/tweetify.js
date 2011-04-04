/*
 * tweetify.js - version 0.0.3
 * copyright 2009 Alex Brem <alex@fluktuation.net>
 * modified 2011 Evan Wheeler <evanmwheeler@gmail.com>
 * license: http://www.opensource.org/licenses/mit-license.php
 */

(function() {

  window.Tweetify || (window.Tweetify = {
    url: 'http://localhost:8080/',
    //url: 'http://snptz.com/',
    search_path: 'tag/',
    regex: {
      linkify: /https?:\/\/[a-z0-9-_]+\.[a-z0-9-_:%&\?\/.=]+/gi,
      hashify: /\B#([\w_]\w[-=~+.:*^\w]+\b(?![-a-z0-9+&@#\/%=~_ ]*?">?))/gi,
      userify: /\B@([-=~+.:*^\w]+\b)/gi
    }
  });

  String.tweetify || (String.prototype.tweetify = function() {
    return this.linkify().hashify().userify();
  });

  String.linkify || (String.prototype.linkify = function() {
    return this.replace(Tweetify.regex.linkify, '<a class="tweetified-link" href="$&">$&</a>');
  });

  String.hashify || (String.prototype.hashify = function() {
    return this.replace(Tweetify.regex.hashify, '<a class="tag-link" href="' + Tweetify.url + Tweetify.search_path + '$1">$&</a>');
  });

  String.userify || (String.prototype.userify = function() {
    return this.replace(Tweetify.regex.userify, '<a class="tweetified-user" href="' + Tweetify.url + '$1">$&</a>');
  });

  if (window.jQuery) {
    jQuery.extend({
      tweetify: function(s) { return s.tweetify() },
      linkify:  function(s) { return s.linkify()  },
      hashify:  function(s) { return s.hashify()  },
      userify:  function(s) { return s.userify()  }
    });
    jQuery.fn.extend({ tweetify: function() {
      this.html(this.html().tweetify()); return this; }
    });
  }

})();
