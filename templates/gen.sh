#!/bin/bash

# common pages
python apply_template.py --template body.template --content common/overview.tmpl > ../browser/index.html
python apply_template.py --template body.template --content common/people.tmpl > ../browser/people.html
python apply_template.py --template body.template --content common/company.tmpl > ../browser/company.html
python apply_template.py --template body.template --content common/country.tmpl > ../browser/country.html
python apply_template.py --template body.template --content common/repository.tmpl > ../browser/repository.html
python apply_template.py --template body.template --content common/domain.tmpl > ../browser/domain.html
python apply_template.py --template body.template --content common/data_sources.tmpl > ../browser/data_sources.html
python apply_template.py --template body.template --content common/project_map.tmpl > ../browser/project_map.html
python apply_template.py --template body.template --content common/project.tmpl > ../browser/project.html
python apply_template.py --template body.template --content common/demographics.tmpl > ../browser/demographics.html
python apply_template.py --template body.template.releases --content common/releases.tmpl > ../browser/release.html
python apply_template.py --template body.template --content common/filter.tmpl > ../browser/filter.html
python apply_template.py --template body.template --content common/project_comparison.tmpl > ../browser/project_comparison.html
python apply_template.py --template body.template --content common/organizations.tmpl > ../browser/organizations.html

cp common/footer.tmpl ../browser/footer.html
cp common/navbar.tmpl ../browser/navbar.html

# scm
python apply_template.py --template body.template.events --content scm/events.tmpl > ../browser/scm-events.html

# its
python apply_template.py --template body.template --content its/overview.tmpl > ../browser/its.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel its-companies > ../browser/its-companies.html
python apply_template.py --template body.template --content its/contributors.tmpl > ../browser/its-contributors.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel its-countries > ../browser/its-countries.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel its-domains > ../browser/its-domains.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel its-projects > ../browser/its-projects.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel its-repos > ../browser/its-repos.html
python apply_template.py --template body.template --content its/states.tmpl > ../browser/its-states.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel its-organizations > ../browser/its-organizations.html

# its_1
python apply_template.py --template body.template --content its_1/overview.tmpl > ../browser/its_1.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel its_1-companies > ../browser/its_1-companies.html
python apply_template.py --template body.template --content its_1/contributors.tmpl > ../browser/its_1-contributors.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel its_1-countries > ../browser/its_1-countries.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel its_1-domains > ../browser/its_1-domains.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel its_1-projects > ../browser/its_1-projects.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel its_1-repos > ../browser/its_1-repos.html
python apply_template.py --template body.template --content its_1/states.tmpl > ../browser/its_1-states.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel its_1-organizations > ../browser/its_1-organizations.html

# its_1 - maniphest
#python apply_template.py --template body.template --content maniphest/overview.tmpl > ../browser/maniphest.html
#python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel maniphest-companies > ../browser/maniphest-companies.html
#python apply_template.py --template body.template --content maniphest/contributors.tmpl > ../browser/maniphest-contributors.html
#python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel maniphest-countries > ../browser/maniphest-countries.html
#python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel maniphest-domains > ../browser/maniphest-domains.html
#python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel its_1-projects > ../browser/maniphest-projects.html
#python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel its_1-repos > ../browser/maniphest-repos.html

# irc
python apply_template.py --template body.template --content irc/overview.tmpl > ../browser/irc.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel irc-repos > ../browser/irc-repos.html
python apply_template.py --template body.template --content irc/contributors.tmpl > ../browser/irc-contributors.html

# mls
python apply_template.py --template body.template --content mls/overview.tmpl > ../browser/mls.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel mls-companies > ../browser/mls-companies.html
python apply_template.py --template body.template --content mls/contributors.tmpl > ../browser/mls-contributors.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel mls-countries > ../browser/mls-countries.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel mls-domains > ../browser/mls-domains.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel mls-projects > ../browser/mls-projects.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel mls-repos > ../browser/mls-repos.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel mls-organizations > ../browser/mls-organizations.html

# qaforums
python apply_template.py --template body.template --content qaforums/overview.tmpl > ../browser/qaforums.html
python apply_template.py --template body.template --content qaforums/contributors.tmpl > ../browser/qaforums-contributors.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel qaforums-tags > ../browser/qaforums-tags.html

# scm
python apply_template.py --template body.template --content scm/overview.tmpl > ../browser/scm.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel scm-companies > ../browser/scm-companies.html
python apply_template.py --template body.template --content scm/companies-summary.tmpl > ../browser/scm-companies-summary.html
python apply_template.py --template body.template --content scm/contributors.tmpl > ../browser/scm-contributors.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel scm-countries > ../browser/scm-countries.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel scm-domains > ../browser/scm-domains.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel scm-projects > ../browser/scm-projects.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel scm-repos > ../browser/scm-repos.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel scm-organizations > ../browser/scm-organizations.html

# scr (Github)
#python apply_template.py --template body.template --content scr_github/overview.tmpl > ../browser/scr.html
#python apply_template.py --template body.template --content scr_github/contributors.tmpl > ../browser/scr-contributors.html

#scr (gerrit)
python apply_template.py --template body.template --content scr_gerrit/overview.tmpl > ../browser/scr.html
python apply_template.py --template body.template --content scr_gerrit/contributors.tmpl > ../browser/scr-contributors.html

#scr (standard)
python apply_template.py --template body.template --content scr/backlog.tmpl > ../browser/scr-backlog.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel scr-companies > ../browser/scr-companies.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel scr-countries > ../browser/scr-countries.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel scr-projects > ../browser/scr-projects.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel scr-repos > ../browser/scr-repos.html
python build_panel.py --template body.template --content common/list-of-filters.tmpl --conf conf/main.conf --panel scr-organizations > ../browser/scr-organizations.html

# wiki
python apply_template.py --template body.template --content wiki/overview.tmpl > ../browser/wiki.html
python apply_template.py --template body.template --content wiki/contributors.tmpl > ../browser/wiki-contributors.html

# downloads
python apply_template.py --template body.template --content downloads/overview.tmpl > ../browser/downloads.html

# forge
python apply_template.py --template body.template --content forge/overview.tmpl > ../browser/forge.html
python apply_template.py --template body.template --content forge/contributors.tmpl > ../browser/forge-contributors.html

# meetup
python apply_template.py --template body.template --content meetup/overview.tmpl > ../browser/meetup.html
python apply_template.py --template body.template --content meetup/past-meetings.tmpl > ../browser/meetup-past_meetings.html
python apply_template.py --template body.template --content meetup/next-meetings.tmpl > ../browser/meetup-next_meetings.html
python apply_template.py --template body.template --content meetup/group.tmpl > ../browser/meetup-group.html

# dockerhub
python apply_template.py --template body.template --content dockerhub/overview.tmpl > ../browser/dockerhub.html
