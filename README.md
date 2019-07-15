
# Ranked Choice Vote Tabulator
Name says it all.

## Installation
Clone this repository, then install globally using `setuptools`'s `develop`
keyword.

```bash
$ git clone https://github.com/apizzimenti/Ranked.git
$ cd Ranked
$ python setup.py develop
```

## Use
Using this package is relatively easy:

```python
from Ranked import Election

...

# Some list of ballots (in this case, just one ballot) and a list of candidates.
ballots = [ { "ranking": ["A", "B", "C"] } ]
candidates = ["A", "B", "C"]

# We can create a new Election object this way,
e = Election(ballots=ballots, candidates=candidates)

# or this way.
e = Election()
e.add_candidates(candidates)

for ballot in ballots:
    e.add_ballot(ballot)

...

# Run a single-winner ranked-choice vote simulation.
e.single_winner_rcv()

# Now you can access a winner!
winner = e.winner

# Make a Sankey vote transfer diagram, for use with https://sankey.csaladen.es/.
e.sankey()
```