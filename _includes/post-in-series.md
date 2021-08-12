{% if page.series %}
    {% assign posts = site.posts | reverse %}
    {% assign i = 0 %}
    {% capture list %}
        <ol>
            {% for post in posts %}
                {% if post.series == page.series %}
                    {% assign i = i | plus: 1%}
                    {% if page.url == post.url %}
                        {% assign postnr = i %}
                        <li><span class="me">{{post.title}}</span><span class="date">{{post.date | date: "%B %d, %Y" }}</span></li>
                    {% else %}
                        <li><a href="{{post.url}}">{{post.title}}</a><span class="date">{{post.date | date: "%B %d, %Y" }}</span></li>
                    {% endif %}
                {% endif %}
            {% endfor %}
        </ol>
    {% endcapture %}

    <div class="series">
        <div>This post is post {{postnr}} of a (so far) {{i}}-part series on <span class="seriesname">"{{page.series}}"</span>.</div>
        {{list}}
    </div>
{% endif %}
