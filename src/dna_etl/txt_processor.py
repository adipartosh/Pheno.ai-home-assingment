from typing import List, Dict, Any, Union
from collections import Counter
# ALL FUNCTIONS WORKING ON LIST OF STR (THAT WAS PARSED FROM TXT)


def gc_content(sequence: str) -> float:
    """
    Compute GC percentage for a single DNA sequence.
    Assumes valid input (A/C/G/T only, non-empty).
    :param sequence: DNA sequence string
    :return: GC content percentage float
    """
    seq = sequence.strip()
    gc = seq.count("G") + seq.count("C")
    return round(gc * 100.0 / len(seq), 2)


def codons_freq(sequence: str) -> Dict[str, int]:
    """
    Compute codon frequency for a single DNA sequence.
    Ignores incomplete codons at the end of the sequence.
    :param sequence: DNA sequence string
    :return: Dict mapping codons to their counts
    """
    length = len(sequence) - (len(sequence) % 3)  # ignore incomplete codon
    # Build list of triplets
    codon_list: List[str] = []
    i = 0
    while i < length:
        triplet = sequence[i:i+3]   # three-letter codon
        codon_list.append(triplet)
        i += 3
    # Count frequencies of each codon
    counts = Counter(codon_list)
    return dict(counts)


def calculate_per_sequence(sequences_lst: List[str]) -> List[Dict[str, Any]]:
    """
    For each sequence, compute GC% and codon frequency.
    Returns a list like:
      [{"gc_content": <float>, "codons": {<codon>: <count>, ...}}, ...]
    :param sequences_lst: List of DNA sequence strings
    :return: List of dictionaries with GC content and codon frequencies
    """
    results: List[Dict[str, Any]] = []
    for seq in sequences_lst:
        gc = gc_content(seq)          # float
        codons = codons_freq(seq)     # Dict[str, int]
        results.append({"gc_content": gc, "codons": codons})
    return results


def most_common_codon(per_seq_info_lst: List[Dict[str, Any]]) -> str:
    """
    Aggregate codon counts across all sequences (from calculate_per_sequence output)
    and returns the most common codon(s) as a single space-separated string.
    :param per_seq_info_lst: List of per-sequence info dicts
    :return: Most common codon(s) as a space-separated string
    """
    # Merge all per-sequence codon histograms into one counter
    total = Counter()
    for entry in per_seq_info_lst:
        # entry represents a single sequence result:
        # {"gc_content": <float>, "codons": {<codon>: <count>, ...}}
        total.update(entry["codons"])  # adds each codon count into the total

    max_count = -1
    winners: List[str] = []
    for codon, cnt in total.items():
        if cnt > max_count:
            max_count = cnt
            winners = [codon]
        elif cnt == max_count:
            winners.append(codon)

    winners.sort()  # deterministic order
    return " ".join(winners)


def lcs_two_strings(m: str, n: str) -> (str, int):
    str1 = list(m)
    str2 = list(n)

    # Create a 2D array to store lengths of longest common subsequence.
    dp = [[0] * (len(str2) + 1) for _ in range(len(str1) + 1)]

    max_length = 0
    end_i = 0  # end index of LCS in str1

    # Iterate over each position in the matrix
    for i in range(1, len(str1) + 1):
        for j in range(1, len(str2) + 1):

            # If characters are equal
            if str1[i - 1] == str2[j - 1]:
                # Get the number from diagonally opposite
                # and add 1
                dp[i][j] = dp[i - 1][j - 1] + 1

                if dp[i][j] > max_length:
                    max_length = dp[i][j]
                    end_i = i
    value = m[end_i - max_length:end_i]

    return value, max_length


def lcs(sequences_lst: List[str]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    finds the longest common string between two DNA sequences- a single longest
    subsequence that appears in two (or more) sequences.
    :param sequences_lst: List of DNA sequence strings
    :return: A tuple containing the longest common subsequence string,
                its length, and a list of the indexes of the sequences in which it appears
    """
    n = len(sequences_lst)
    best_len = 0

    # Keep winners in first-seen order without duplicates
    winners_lst: List[str] = []
    seen_values: set[str] = set()

    for i in range(n):
        s1 = sequences_lst[i]
        for j in range(i + 1, n):
            s2 = sequences_lst[j]
            value, length = lcs_two_strings(s1, s2)  # returns (substring, length)

            if length == 0:
                continue

            if length > best_len:
                # New best found → reset the winners to only this value
                best_len = length
                winners_lst = []
                seen_values.clear()
                winners_lst.append(value)
                seen_values.add(value)

            elif length == best_len:
                # Same best length → include this value if not already included
                if value not in seen_values:
                    winners_lst.append(value)
                    seen_values.add(value)

    # Build output records: for each winning substring, collect ALL sequences (1-based) containing it
    results: List[Dict[str, Any]] = []
    for val in winners_lst:
        indices = [idx + 1 for idx, s in enumerate(sequences_lst) if val in s]
        results.append({"value": val, "sequences": indices, "length": best_len})

    # If only one winner → return a single dict; otherwise return a list of dicts
    return results[0] if len(results) == 1 else results


def build_txt_output(per_seq, most_common, lcs_info) -> Dict[str, Any]:
    """
    Assemble the TXT block to match the assignment example:
    :param per_seq: Output of calculate_per_sequence() - List[Dict[str, Any]]
    :param most_common: Output of most_common_codon() - str
    :param lcs_info: Output of lcs() - Dict[str, Any] or List[Dict[str, Any]]
    :return: Dictionary with keys "sequences", "most_common_codon", "lcs"
    """
    return {
        "sequences": per_seq,
        "most_common_codon": most_common,
        "lcs": lcs_info,
    }
