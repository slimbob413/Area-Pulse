---
layout: default
title: Home
---

# Area Pulse

_Tracking Nigeria's political, economic, and tech discourse._

## Latest Posts

<ul>
  {% for post in site.pages %}
    {% if post.path contains 'posts/' %}
      <li>
        <a href="{{ post.url }}">{{ post.title }}</a> - {{ post.date | date: "%b %d, %Y" }}
      </li>
    {% endif %}
  {% endfor %}
</ul> 