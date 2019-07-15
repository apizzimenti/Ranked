
import random
import math
import json


class Election():
    """
    Simulates a ranked-choice voting election.
    """
    def __init__(self, ballots=[], candidates=[]):
        """
        Initializes the Election object.

        :ballots=[]: List of ballots. Each ballot is a dictionary with two
        properties: the weight of the ballot and the ranking of the candidates.
        Defaults to an empty list.
        :candidates=[]: List of candidates. Defaults to an empty dict.
        :winner=None: Winner of the election. Once a single-winner election is
        simulated, this will map to the winner of that election.
        """
        self.ballots = ballots
        self.candidates = { candidate: [] for candidate in candidates }
        self.winner = None
        self.eliminated = set()
        self.number_of_candidates = 0

        # Create the template for the Sankey diagram.
        self.sankey_obj = {
            "nodes": [],
            "links": []
        }


    def validate(self, ballot):
        """
        Validates a ballot has the right properties, those properties map
        to the correct types, and the lists of candidates in the rankings
        and in the list of candidates in this election are the same.

        :ballot: Dictionary or other object type.
        """
        raise NotImplementedError


    def add_ballot(self, ballot):
        """
        Adds a ballot to the list of ballots.

        :ballot: Adds a ballot to the list of ballots.
        """
        # self.validate(ballot)
        self.ballots.append(ballot)


    def resolve_tie_random(self):
        """
        Resolves a tie by randomly choosing a candidate to eliminate.
        """
        reverse_ranked_candidates = list(reversed(self.sort_candidates()))
        tally = len(self.candidates[reverse_ranked_candidates[0]])
        tied_candidates = [reverse_ranked_candidates[0]]

        for candidate in reverse_ranked_candidates:
            if len(self.candidates[candidate]) == tally and candidate not in tied_candidates:
                tied_candidates.append(candidate)

        return random.choice(tied_candidates)


    def add_candidates(self, candidates):
        """
        Adds candidates to the election.
        
        :candidates: List of candidates.
        """
        # Shuffle candidates, which are made unique by converting to a set
        # then back again.
        candidates = list(set(candidates))
        self.riffle(candidates)

        for candidate in candidates:
            self.candidates[candidate] = []


    def assign_ballots(self):
        """
        Assigns ballots to candidates.
        """
        self.number_of_candidates = len(self.candidates)

        for ballot in self.ballots:
            first_choice = ballot["ranking"][0]
            self.candidates[first_choice].append(ballot)


    def sort_candidates(self, sankey_layer=0):
        """
        Sorts the candidates by the number of ballots.

        :returns: List of candidates sorted by number of assigned ballots.
        """
        return sorted(self.candidates, key=lambda g: -len(self.candidates[g]))


    def single_winner_rcv(self):
        """
        Simulates an RCV election.
        """
        # Assign initial ballots.
        self.assign_ballots()

        # Create a counter to denote the Sankey diagram layer.
        sankey_layer = 1

        # Add our initial set of candidates. Also create a mapping for each
        # candidate to their starting values.
        self.sankey_obj["nodes"] += [
            { "name": candidate, "layer": sankey_layer, "value": len(self.candidates[candidate]) }
            for candidate in self.candidates if len(self.candidates[candidate]) > 0
        ]

        # In order to sim the election, we need to lay out a few well-
        # defined rules. For each round of ballot reassignment:
        #
        #   1.  order each candidate according to how many ballots they
        #       have been awarded;
        #   2.  the candidate in last place is added to the list of
        #       eliminated candidates;
        #   3.  currently, ties are resolved by randomly picking a
        #       candidate to eliminate;
        #   4.  for all existing ballots, each ballot is reassigned to
        #       its next available choice; i.e. each ballot is assigned to
        #       the highest-ranked choice *not* in the list of eliminated
        #       candidates.

        while len(self.eliminated) < self.number_of_candidates - 1:
            # Get the last-place candidate.
            last_place = self.resolve_tie_random()
            
            # Now, we eliminate the last-place candidate. We then perform a
            # check on whether the candidate being eliminated actually has some
            # ballots awarded to them. If they don't, we can skip all of the
            # below.
            self.eliminated.add(last_place)
            if len(self.candidates[last_place]) == 0:
                del self.candidates[last_place]
                continue
            
            # Create a mapping that preserves the vote tallies for the previous
            # round.
            starting_values = {
                candidate: len(self.candidates[candidate].copy())
                for candidate in self.candidates
            }

            # Next, we only want to look in the ballots awarded to the
            # last-place finisher; for each of these ballots, reassign them
            # to the ballot's next-highest-ranked candidate that hasn't
            # been already eliminated. Also, if all the candidates on a
            # ballot's preference list *have* been eliminated (or there isn't
            # a complete preference listed on the ballot), then the ballot
            # is considered exhausted and does not get counted in the final
            # tally.

            # Create a dictionary containing the number of ballots transferred
            # from the last-place candidates to the remaining candidates.
            transfers = {}

            for ballot in self.candidates[last_place]:
                for candidate in ballot["ranking"]:
                    if candidate not in self.eliminated:
                        # Record the transfer and transfer the votes!
                        if transfers.get(candidate, None) is not None:
                            transfers[candidate] += 1
                        else:
                            transfers[candidate] = 1
                        self.candidates[candidate].append(ballot)
                        break

            # Delete last-place candidate.
            del self.candidates[last_place]

            # Do some dumb stuff for the Sankey diagram. Why can't this tool
            # use the *names* of the nodes to index them instead of the order
            # in which they were added?!?! It makes no sense, but whatever.
            sankey_layer += 1

            # Add new nodes to the Sankey diagram.
            self.sankey_obj["nodes"] += [
                { "name": candidate, "layer": sankey_layer }
                for candidate in self.candidates if candidate not in self.eliminated
            ]

            # Now we want to add some links to this diagram of ours. How do we
            # do this, you ask? In a completely nonsensical, roundabout way that
            # sucks because SOMEbody couldn't figure out how to properly program
            # a Sankey diagram generator. If it's not already clear, I'm really
            # upset about this.
            links = []

            # Add self-links.
            for candidate in self.candidates:
                if candidate != last_place:
                    fake_node_from = { "name": candidate, "layer": sankey_layer - 1 }
                    fake_node_to = { "name": candidate, "layer": sankey_layer }

                    if sankey_layer < 3:
                        fake_node_from["value"] = starting_values[candidate]

                    index_from = self.sankey_obj["nodes"].index(fake_node_from)
                    index_to = self.sankey_obj["nodes"].index(fake_node_to)
                    votes = starting_values[candidate]
                    link = { "source": index_from, "target": index_to, "value": votes }
                    links.append(link)

            # Add real links.
            for candidate in transfers:
                fake_node_from = { "name": last_place, "layer": sankey_layer - 1 }
                fake_node_to = { "name": candidate, "layer": sankey_layer }

                if sankey_layer < 3:
                    fake_node_from["value"] = starting_values[last_place]

                index_from = self.sankey_obj["nodes"].index(fake_node_from)
                index_to = self.sankey_obj["nodes"].index(fake_node_to)
                votes = transfers[candidate]
                link = { "source": index_from, "target": index_to, "value": votes }
                links.append(link)

            # Add our links to the Sankey object.
            self.sankey_obj["links"] += links

        self.winner = list(self.candidates.keys())[0]


    def condorcet(self):
        raise NotImplementedError


    def riffle(self, item):
        """
        Finds the proper number of riffle shuffles required to minimize
        the variation distance across a group of shuffles, then shuffles
        the thing that number of times. From Bayer and Diaconis' result on
        card-shuffling.

        :item:  The thing we want to shuffle.
        """
        shuffles = (3/2) * math.log2(len(item)) + random.randrange(0, len(item))

        for i in range(0, math.ceil(shuffles)):
            random.shuffle(item)


    def droop(self, seats, winner):
        """
        Determines whether the winner of a given election satisfies
        the Droop quota.

        :seats:     How many seats are we electing?
        :returns:   Boolean; does the winner of this election satistfy the
        droop quota?
        """
        return len(self.candidates[self.winner]) > math.floor(len(self.ballots) / seats)


    def sankey(self, filepath="./data/sankey.json"):
        """
        Saves this `Election` object as json, which can be inputted into the
        Sankey Diagram tool at `https://sankey.csaladen.es/`.

        :filepath="./data/sankey.json": Filepath.
        :returns: Nothing.
        """
        with open(filepath, "w") as f:
            f.write(json.dumps({ "sankey": self.sankey_obj }, indent=2))

    
    def __repr__(self):
        """
        Returns a string representation of this Election object.
        
        :returns: A string.
        """
        num_candidates = self.number_of_candidates
        num_ballots = len(self.ballots)
        active_candidates = num_candidates - len(self.eliminated)
        active_ballots = num_ballots - sum([len(self.candidates[c]) for c in self.candidates])

        status = (
            f"Number of candidates: {num_candidates}\n"
            f"Number of ballots: {num_ballots}\n"
            f"Remaining candidates: {active_candidates}\n"
            f"Exhausted ballots: {num_ballots - active_ballots}"
        )

        return status
