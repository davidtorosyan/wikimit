#!/usr/bin/env python

import os
import os.path
import xml.dom.minidom
from collections import OrderedDict
from dataclasses import dataclass
import subprocess
import json
import dataclasses
import datetime
import io
import time
import sys

import requests

# constants

WIKI_BASE = "https://en.wikipedia.org"

# classes

@dataclass
class Commit:
    message: str
    author: str
    description: str
    content: str
    date: str
    info: dict

@dataclass
class PageInfo:
    id: str
    url: str
    title: str
    language: str
    highest_known_revision_id: str
    highest_known_revision_timestamp: str
    synced_revision_id: str
    synced_revision_timestamp: str
    last_sync: str

# main

def main():
    if len(sys.argv) < 3:
        sys.exit('Usage: python proof.py title outdir')
    title = sys.argv[1]
    path = sys.argv[2]
    process_all(title, path)

def process_all(title, path):
    done = False
    while not done:
        done = process(title, path, limit=100)
    print('Done!')
    print_clocks()

def process(title, path, limit):
    chdir(path)
    current_info = get_info()
    current = download_history(title, current=True)
    print('Querying wikipedia...')

    start_clock('wiki')
    history = download_history(title, offset=current_info['synced_revision_timestamp'] if current_info else None, limit=limit)
    stop_clock('wiki')

    info = parse_current(current)
    if not current_info:
        first_setup(info)
    commits = parse_history(history)
    if not commits:
        print('No more work to do!')
        return True
    print('Adding {} commits...'.format(len(commits)))

    start_clock('git')
    add_commits(path, info, commits)
    stop_clock('git')

    return info.synced_revision_id == info.highest_known_revision_id

# perf

CLOCKS = {}
ELAPSED = {}

def start_clock(name):
    CLOCKS[name] = time.perf_counter()

def stop_clock(name):
    elapsed = time.perf_counter() - CLOCKS[name]
    ELAPSED[name] = ELAPSED.get(name, 0) + elapsed
    print('{} took {:.2f} seconds'.format(name, elapsed))
    return elapsed

def print_clocks():
    for name, elapsed in ELAPSED.items():
        print('{} took a total of {:.2f} seconds'.format(name, elapsed))

# local

def chdir(path):
    if not os.path.exists(path):
        os.mkdir(path)
    os.chdir(path)

def get_info():
    info_name = 'info.json'
    if not os.path.exists(info_name):
        return None
    with io.open(info_name, 'r', encoding='utf8') as file:
        return json.loads(file.read())

def add_commits(path, info, commits):
    for commit in commits:
        update_files(info, commit)
        git_commit(commit)

def first_setup(info):
    git_init()

    article_name = 'article.xml'
    info_name = 'info.json'
    readme_name = 'README.md'
    license_name = 'LICENSE'

    info.synced_revision_id = ''
    info.synced_revision_timestamp = ''
    info.last_sync = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    with io.open(article_name, 'w', encoding='utf8') as file:
        pass
    with io.open(info_name, 'w', encoding='utf8') as file:
        file.write(json.dumps(info, cls=EnhancedJSONEncoder, indent=4))
    with io.open(readme_name, 'w', encoding='utf8') as file:
        file.write(README_TEMPLATE.format(info.title, info.url))
    with io.open(license_name, 'w', encoding='utf8') as file:
        file.write(LICENSE_CC_BY_SA)

    git_add(article_name)
    git_add(info_name)
    git_add(readme_name)
    git_add(license_name)

    git_commit_initial()

def update_files(info, commit):
    article_name = 'article.xml'
    info_name = 'info.json'

    info.synced_revision_id = commit.info['id']
    info.synced_revision_timestamp = commit.date
    info.last_sync = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    with io.open(article_name, 'w', encoding='utf8') as file:
        file.write(commit.content)
    with io.open(info_name, 'w', encoding='utf8') as file:
        file.write(json.dumps(info, cls=EnhancedJSONEncoder, indent=4))

    git_add(article_name)
    git_add(info_name)

# git

def git_repo_root():
    return subprocess.Popen([
        'git',
        'rev-parse',
        '--show-toplevel'
    ], stdout=subprocess.PIPE).communicate()[0].rstrip().decode('utf-8')

def git_init():
    subprocess.Popen([
        'git',
        'init',
        '--initial-branch', 'main',
    ], stdout=subprocess.PIPE).communicate()

def git_add(name):
    subprocess.Popen([
        'git',
        'add',
        name,
    ], stdout=subprocess.PIPE).communicate()

def git_commit_initial():
    subprocess.Popen([
        'git',
        'commit',
        '-m', 'Initial commit'
    ], stdout=subprocess.PIPE).communicate()

def git_commit(commit):
    subprocess.Popen([
        'git',
        'commit',
        '-m', commit.message,
        '-m', commit.description,
        '--date', commit.date,
        '--author', commit.author
    ], stdout=subprocess.PIPE).communicate()

# convert

def parse_current(current):
    doc = xml.dom.minidom.parseString(current)
    page = doc.getElementsByTagName('page')[0]
    revision = doc.getElementsByTagName('revision')[0]
    title = getChildText(page, 'title')
    url = '{}/wiki/{}'.format(WIKI_BASE, title)
    return PageInfo(
        id=getChildText(page, 'id'),
        url=url,
        title=title,
        language='en',
        highest_known_revision_id=getChildText(revision, 'id'),
        highest_known_revision_timestamp=getChildText(revision, 'timestamp'),
        synced_revision_id='',
        synced_revision_timestamp='',
        last_sync='')

def parse_history(history):
    doc = xml.dom.minidom.parseString(history)
    revisions = doc.getElementsByTagName('revision')
    return [revision_to_commit(r) for r in revisions]

def revision_to_commit(revision):
    contributor = revision.getElementsByTagName('contributor')[0]
    contributor_username = getChildText(contributor, 'username')
    contributor_id = getChildText(contributor, 'id')
    contributor_ip = getChildText(contributor, 'ip')

    message = getChildText(revision, 'comment')
    author = '{} <{}>'.format(contributor_username, contributor_id) if contributor_username else '{} <IP>'.format(contributor_ip)
    date = getChildText(revision, 'timestamp')
    info = OrderedDict([
        ('id', getChildText(revision, 'id')),
        ('timestamp', date),
        ('contributor_username', contributor_username),
        ('contributor_id', contributor_id),
        ('contributor_ip', contributor_ip),
        ('minor', 'True' if hasChild(revision, 'minor') else 'False'),
        ('model', getChildText(revision, 'model')),
        ('format', getChildText(revision, 'format')),
        ('sha1', getChildText(revision, 'sha1')),
    ])
    description = '\n'.join(['{}: {}'.format(k, v) for k, v in info.items() if v])
    return Commit(
        message=message if message else '.',
        author=author,
        description=description,
        content=getChildText(revision, 'text'),
        date=date,
        info=info)

# wiki

def download_history(title, current=False, offset=1, limit=5):
    # See parameters here:
    # https://www.mediawiki.org/wiki/Manual:Parameters_to_Special:Export
    url = '{}/w/index.php'.format(WIKI_BASE)
    params = {
        'title': 'Special:Export',
        'pages': title,
        'action': 'submit',
    }
    if current:
        params['curonly'] = 'true'
    else:
        params['offset'] = offset
        params['limit'] = limit
    response = requests.post(url, params=params)
    return response.content

# XML helpers

def hasChild(node, tag):
    elems = node.getElementsByTagName(tag)
    return len(elems) > 0

def getChildText(node, tag):
    elems = node.getElementsByTagName(tag)
    return getText(elems[0].childNodes) if elems else ''

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

# json

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)

# templates

README_TEMPLATE = """# {} [wikimit]

## Overview

This repo is a [wikimit](https://github.com/davidtorosyan/wikimit) generated mirror of this Wikipedia page: {}

## Usage

View the [article](article.xml), including its revision history, or the [sync info](info.json).

## License

Like all [Wikipedia derivatives](https://en.wikipedia.org/wiki/Wikipedia:Mirrors_and_forks), this repo is licensed under a
[Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/).
"""

LICENSE_CC_BY_SA = """Attribution-ShareAlike 4.0 International

=======================================================================

Creative Commons Corporation ("Creative Commons") is not a law firm and
does not provide legal services or legal advice. Distribution of
Creative Commons public licenses does not create a lawyer-client or
other relationship. Creative Commons makes its licenses and related
information available on an "as-is" basis. Creative Commons gives no
warranties regarding its licenses, any material licensed under their
terms and conditions, or any related information. Creative Commons
disclaims all liability for damages resulting from their use to the
fullest extent possible.

Using Creative Commons Public Licenses

Creative Commons public licenses provide a standard set of terms and
conditions that creators and other rights holders may use to share
original works of authorship and other material subject to copyright
and certain other rights specified in the public license below. The
following considerations are for informational purposes only, are not
exhaustive, and do not form part of our licenses.

     Considerations for licensors: Our public licenses are
     intended for use by those authorized to give the public
     permission to use material in ways otherwise restricted by
     copyright and certain other rights. Our licenses are
     irrevocable. Licensors should read and understand the terms
     and conditions of the license they choose before applying it.
     Licensors should also secure all rights necessary before
     applying our licenses so that the public can reuse the
     material as expected. Licensors should clearly mark any
     material not subject to the license. This includes other CC-
     licensed material, or material used under an exception or
     limitation to copyright. More considerations for licensors:
	wiki.creativecommons.org/Considerations_for_licensors

     Considerations for the public: By using one of our public
     licenses, a licensor grants the public permission to use the
     licensed material under specified terms and conditions. If
     the licensor's permission is not necessary for any reason--for
     example, because of any applicable exception or limitation to
     copyright--then that use is not regulated by the license. Our
     licenses grant only permissions under copyright and certain
     other rights that a licensor has authority to grant. Use of
     the licensed material may still be restricted for other
     reasons, including because others have copyright or other
     rights in the material. A licensor may make special requests,
     such as asking that all changes be marked or described.
     Although not required by our licenses, you are encouraged to
     respect those requests where reasonable. More_considerations
     for the public:
	wiki.creativecommons.org/Considerations_for_licensees

=======================================================================

Creative Commons Attribution-ShareAlike 4.0 International Public
License

By exercising the Licensed Rights (defined below), You accept and agree
to be bound by the terms and conditions of this Creative Commons
Attribution-ShareAlike 4.0 International Public License ("Public
License"). To the extent this Public License may be interpreted as a
contract, You are granted the Licensed Rights in consideration of Your
acceptance of these terms and conditions, and the Licensor grants You
such rights in consideration of benefits the Licensor receives from
making the Licensed Material available under these terms and
conditions.


Section 1 -- Definitions.

  a. Adapted Material means material subject to Copyright and Similar
     Rights that is derived from or based upon the Licensed Material
     and in which the Licensed Material is translated, altered,
     arranged, transformed, or otherwise modified in a manner requiring
     permission under the Copyright and Similar Rights held by the
     Licensor. For purposes of this Public License, where the Licensed
     Material is a musical work, performance, or sound recording,
     Adapted Material is always produced where the Licensed Material is
     synched in timed relation with a moving image.

  b. Adapter's License means the license You apply to Your Copyright
     and Similar Rights in Your contributions to Adapted Material in
     accordance with the terms and conditions of this Public License.

  c. BY-SA Compatible License means a license listed at
     creativecommons.org/compatiblelicenses, approved by Creative
     Commons as essentially the equivalent of this Public License.

  d. Copyright and Similar Rights means copyright and/or similar rights
     closely related to copyright including, without limitation,
     performance, broadcast, sound recording, and Sui Generis Database
     Rights, without regard to how the rights are labeled or
     categorized. For purposes of this Public License, the rights
     specified in Section 2(b)(1)-(2) are not Copyright and Similar
     Rights.

  e. Effective Technological Measures means those measures that, in the
     absence of proper authority, may not be circumvented under laws
     fulfilling obligations under Article 11 of the WIPO Copyright
     Treaty adopted on December 20, 1996, and/or similar international
     agreements.

  f. Exceptions and Limitations means fair use, fair dealing, and/or
     any other exception or limitation to Copyright and Similar Rights
     that applies to Your use of the Licensed Material.

  g. License Elements means the license attributes listed in the name
     of a Creative Commons Public License. The License Elements of this
     Public License are Attribution and ShareAlike.

  h. Licensed Material means the artistic or literary work, database,
     or other material to which the Licensor applied this Public
     License.

  i. Licensed Rights means the rights granted to You subject to the
     terms and conditions of this Public License, which are limited to
     all Copyright and Similar Rights that apply to Your use of the
     Licensed Material and that the Licensor has authority to license.

  j. Licensor means the individual(s) or entity(ies) granting rights
     under this Public License.

  k. Share means to provide material to the public by any means or
     process that requires permission under the Licensed Rights, such
     as reproduction, public display, public performance, distribution,
     dissemination, communication, or importation, and to make material
     available to the public including in ways that members of the
     public may access the material from a place and at a time
     individually chosen by them.

  l. Sui Generis Database Rights means rights other than copyright
     resulting from Directive 96/9/EC of the European Parliament and of
     the Council of 11 March 1996 on the legal protection of databases,
     as amended and/or succeeded, as well as other essentially
     equivalent rights anywhere in the world.

  m. You means the individual or entity exercising the Licensed Rights
     under this Public License. Your has a corresponding meaning.


Section 2 -- Scope.

  a. License grant.

       1. Subject to the terms and conditions of this Public License,
          the Licensor hereby grants You a worldwide, royalty-free,
          non-sublicensable, non-exclusive, irrevocable license to
          exercise the Licensed Rights in the Licensed Material to:

            a. reproduce and Share the Licensed Material, in whole or
               in part; and

            b. produce, reproduce, and Share Adapted Material.

       2. Exceptions and Limitations. For the avoidance of doubt, where
          Exceptions and Limitations apply to Your use, this Public
          License does not apply, and You do not need to comply with
          its terms and conditions.

       3. Term. The term of this Public License is specified in Section
          6(a).

       4. Media and formats; technical modifications allowed. The
          Licensor authorizes You to exercise the Licensed Rights in
          all media and formats whether now known or hereafter created,
          and to make technical modifications necessary to do so. The
          Licensor waives and/or agrees not to assert any right or
          authority to forbid You from making technical modifications
          necessary to exercise the Licensed Rights, including
          technical modifications necessary to circumvent Effective
          Technological Measures. For purposes of this Public License,
          simply making modifications authorized by this Section 2(a)
          (4) never produces Adapted Material.

       5. Downstream recipients.

            a. Offer from the Licensor -- Licensed Material. Every
               recipient of the Licensed Material automatically
               receives an offer from the Licensor to exercise the
               Licensed Rights under the terms and conditions of this
               Public License.

            b. Additional offer from the Licensor -- Adapted Material.
               Every recipient of Adapted Material from You
               automatically receives an offer from the Licensor to
               exercise the Licensed Rights in the Adapted Material
               under the conditions of the Adapter's License You apply.

            c. No downstream restrictions. You may not offer or impose
               any additional or different terms or conditions on, or
               apply any Effective Technological Measures to, the
               Licensed Material if doing so restricts exercise of the
               Licensed Rights by any recipient of the Licensed
               Material.

       6. No endorsement. Nothing in this Public License constitutes or
          may be construed as permission to assert or imply that You
          are, or that Your use of the Licensed Material is, connected
          with, or sponsored, endorsed, or granted official status by,
          the Licensor or others designated to receive attribution as
          provided in Section 3(a)(1)(A)(i).

  b. Other rights.

       1. Moral rights, such as the right of integrity, are not
          licensed under this Public License, nor are publicity,
          privacy, and/or other similar personality rights; however, to
          the extent possible, the Licensor waives and/or agrees not to
          assert any such rights held by the Licensor to the limited
          extent necessary to allow You to exercise the Licensed
          Rights, but not otherwise.

       2. Patent and trademark rights are not licensed under this
          Public License.

       3. To the extent possible, the Licensor waives any right to
          collect royalties from You for the exercise of the Licensed
          Rights, whether directly or through a collecting society
          under any voluntary or waivable statutory or compulsory
          licensing scheme. In all other cases the Licensor expressly
          reserves any right to collect such royalties.


Section 3 -- License Conditions.

Your exercise of the Licensed Rights is expressly made subject to the
following conditions.

  a. Attribution.

       1. If You Share the Licensed Material (including in modified
          form), You must:

            a. retain the following if it is supplied by the Licensor
               with the Licensed Material:

                 i. identification of the creator(s) of the Licensed
                    Material and any others designated to receive
                    attribution, in any reasonable manner requested by
                    the Licensor (including by pseudonym if
                    designated);

                ii. a copyright notice;

               iii. a notice that refers to this Public License;

                iv. a notice that refers to the disclaimer of
                    warranties;

                 v. a URI or hyperlink to the Licensed Material to the
                    extent reasonably practicable;

            b. indicate if You modified the Licensed Material and
               retain an indication of any previous modifications; and

            c. indicate the Licensed Material is licensed under this
               Public License, and include the text of, or the URI or
               hyperlink to, this Public License.

       2. You may satisfy the conditions in Section 3(a)(1) in any
          reasonable manner based on the medium, means, and context in
          which You Share the Licensed Material. For example, it may be
          reasonable to satisfy the conditions by providing a URI or
          hyperlink to a resource that includes the required
          information.

       3. If requested by the Licensor, You must remove any of the
          information required by Section 3(a)(1)(A) to the extent
          reasonably practicable.

  b. ShareAlike.

     In addition to the conditions in Section 3(a), if You Share
     Adapted Material You produce, the following conditions also apply.

       1. The Adapter's License You apply must be a Creative Commons
          license with the same License Elements, this version or
          later, or a BY-SA Compatible License.

       2. You must include the text of, or the URI or hyperlink to, the
          Adapter's License You apply. You may satisfy this condition
          in any reasonable manner based on the medium, means, and
          context in which You Share Adapted Material.

       3. You may not offer or impose any additional or different terms
          or conditions on, or apply any Effective Technological
          Measures to, Adapted Material that restrict exercise of the
          rights granted under the Adapter's License You apply.


Section 4 -- Sui Generis Database Rights.

Where the Licensed Rights include Sui Generis Database Rights that
apply to Your use of the Licensed Material:

  a. for the avoidance of doubt, Section 2(a)(1) grants You the right
     to extract, reuse, reproduce, and Share all or a substantial
     portion of the contents of the database;

  b. if You include all or a substantial portion of the database
     contents in a database in which You have Sui Generis Database
     Rights, then the database in which You have Sui Generis Database
     Rights (but not its individual contents) is Adapted Material,

     including for purposes of Section 3(b); and
  c. You must comply with the conditions in Section 3(a) if You Share
     all or a substantial portion of the contents of the database.

For the avoidance of doubt, this Section 4 supplements and does not
replace Your obligations under this Public License where the Licensed
Rights include other Copyright and Similar Rights.


Section 5 -- Disclaimer of Warranties and Limitation of Liability.

  a. UNLESS OTHERWISE SEPARATELY UNDERTAKEN BY THE LICENSOR, TO THE
     EXTENT POSSIBLE, THE LICENSOR OFFERS THE LICENSED MATERIAL AS-IS
     AND AS-AVAILABLE, AND MAKES NO REPRESENTATIONS OR WARRANTIES OF
     ANY KIND CONCERNING THE LICENSED MATERIAL, WHETHER EXPRESS,
     IMPLIED, STATUTORY, OR OTHER. THIS INCLUDES, WITHOUT LIMITATION,
     WARRANTIES OF TITLE, MERCHANTABILITY, FITNESS FOR A PARTICULAR
     PURPOSE, NON-INFRINGEMENT, ABSENCE OF LATENT OR OTHER DEFECTS,
     ACCURACY, OR THE PRESENCE OR ABSENCE OF ERRORS, WHETHER OR NOT
     KNOWN OR DISCOVERABLE. WHERE DISCLAIMERS OF WARRANTIES ARE NOT
     ALLOWED IN FULL OR IN PART, THIS DISCLAIMER MAY NOT APPLY TO YOU.

  b. TO THE EXTENT POSSIBLE, IN NO EVENT WILL THE LICENSOR BE LIABLE
     TO YOU ON ANY LEGAL THEORY (INCLUDING, WITHOUT LIMITATION,
     NEGLIGENCE) OR OTHERWISE FOR ANY DIRECT, SPECIAL, INDIRECT,
     INCIDENTAL, CONSEQUENTIAL, PUNITIVE, EXEMPLARY, OR OTHER LOSSES,
     COSTS, EXPENSES, OR DAMAGES ARISING OUT OF THIS PUBLIC LICENSE OR
     USE OF THE LICENSED MATERIAL, EVEN IF THE LICENSOR HAS BEEN
     ADVISED OF THE POSSIBILITY OF SUCH LOSSES, COSTS, EXPENSES, OR
     DAMAGES. WHERE A LIMITATION OF LIABILITY IS NOT ALLOWED IN FULL OR
     IN PART, THIS LIMITATION MAY NOT APPLY TO YOU.

  c. The disclaimer of warranties and limitation of liability provided
     above shall be interpreted in a manner that, to the extent
     possible, most closely approximates an absolute disclaimer and
     waiver of all liability.


Section 6 -- Term and Termination.

  a. This Public License applies for the term of the Copyright and
     Similar Rights licensed here. However, if You fail to comply with
     this Public License, then Your rights under this Public License
     terminate automatically.

  b. Where Your right to use the Licensed Material has terminated under
     Section 6(a), it reinstates:

       1. automatically as of the date the violation is cured, provided
          it is cured within 30 days of Your discovery of the
          violation; or

       2. upon express reinstatement by the Licensor.

     For the avoidance of doubt, this Section 6(b) does not affect any
     right the Licensor may have to seek remedies for Your violations
     of this Public License.

  c. For the avoidance of doubt, the Licensor may also offer the
     Licensed Material under separate terms or conditions or stop
     distributing the Licensed Material at any time; however, doing so
     will not terminate this Public License.

  d. Sections 1, 5, 6, 7, and 8 survive termination of this Public
     License.


Section 7 -- Other Terms and Conditions.

  a. The Licensor shall not be bound by any additional or different
     terms or conditions communicated by You unless expressly agreed.

  b. Any arrangements, understandings, or agreements regarding the
     Licensed Material not stated herein are separate from and
     independent of the terms and conditions of this Public License.


Section 8 -- Interpretation.

  a. For the avoidance of doubt, this Public License does not, and
     shall not be interpreted to, reduce, limit, restrict, or impose
     conditions on any use of the Licensed Material that could lawfully
     be made without permission under this Public License.

  b. To the extent possible, if any provision of this Public License is
     deemed unenforceable, it shall be automatically reformed to the
     minimum extent necessary to make it enforceable. If the provision
     cannot be reformed, it shall be severed from this Public License
     without affecting the enforceability of the remaining terms and
     conditions.

  c. No term or condition of this Public License will be waived and no
     failure to comply consented to unless expressly agreed to by the
     Licensor.

  d. Nothing in this Public License constitutes or may be interpreted
     as a limitation upon, or waiver of, any privileges and immunities
     that apply to the Licensor or You, including from the legal
     processes of any jurisdiction or authority.


=======================================================================

Creative Commons is not a party to its public
licenses. Notwithstanding, Creative Commons may elect to apply one of
its public licenses to material it publishes and in those instances
will be considered the “Licensor.” The text of the Creative Commons
public licenses is dedicated to the public domain under the CC0 Public
Domain Dedication. Except for the limited purpose of indicating that
material is shared under a Creative Commons public license or as
otherwise permitted by the Creative Commons policies published at
creativecommons.org/policies, Creative Commons does not authorize the
use of the trademark "Creative Commons" or any other trademark or logo
of Creative Commons without its prior written consent including,
without limitation, in connection with any unauthorized modifications
to any of its public licenses or any other arrangements,
understandings, or agreements concerning use of licensed material. For
the avoidance of doubt, this paragraph does not form part of the
public licenses.

Creative Commons may be contacted at creativecommons.org.
"""

# main

if __name__ == '__main__':
    main()