---
layout: archive
title: "CV"
permalink: /cv/
author_profile: true
redirect_from:
  - /resume
---

{% include base_path %}

{% assign cv = site.data.cv %}

<p>
  <a href="{{ base_path }}/files/cv.pdf" class="btn btn--primary"><i class="fa fa-file-pdf-o"></i> Download PDF</a>
  <a href="{{ base_path }}/files/cv.docx" class="btn"><i class="fa fa-file-word-o"></i> Download Word</a>
</p>

<p><em>This CV is generated automatically from structured data; the documents above are rebuilt on every site update.</em></p>

Education
======
<ul>
{% for ed in cv.education %}
  <li>
    <strong>{{ ed.institution }}</strong>{% if ed.location %}, {{ ed.location }}{% endif %}
    <ul>
      {% for deg in ed.degrees %}<li>{{ deg }}</li>{% endfor %}
      {% if ed.note %}<li>{{ ed.note }}</li>{% endif %}
      {% for d in ed.details %}<li><em>{{ d.label }}:</em> {{ d.text }}</li>{% endfor %}
    </ul>
  </li>
{% endfor %}
</ul>

Work experience
======
<ul>
{% for job in cv.experience %}
  <li>
    <strong>{{ job.org }}: {{ job.role }}</strong>{% if job.location %} ({{ job.location }}){% endif %}
    <ul>
      {% if job.note %}<li>{{ job.note }}</li>{% endif %}
      {% if job.dates %}<li>{{ job.dates }}</li>{% endif %}
      {% for b in job.bullets %}<li>{{ b }}</li>{% endfor %}
    </ul>
  </li>
{% endfor %}
</ul>

Skills &amp; Interests
======
<ul>
{% for s in cv.skills %}
  <li><strong>{{ s.label }}:</strong> {{ s.text }}</li>
{% endfor %}
</ul>

Publications
======
  <ul>{% for post in site.publications reversed %}
    {% include archive-single-cv.html %}
  {% endfor %}</ul>

Presentations
======
  <ul>{% for post in site.talks reversed %}
    {% include archive-single-talk-cv.html %}
  {% endfor %}</ul>

Teaching
======
  <ul>{% for post in site.teaching reversed %}
    {% include archive-single-cv.html %}
  {% endfor %}</ul>
