async function fetchAccountData(cc, uid) {
  // GraphQL query
  const query = `
    query AccountManagementPageQuery($cc: String!, $uid: String!) {
      getUser(fbUid: $uid) {
        ...userProfilePage
        __typename
      }
      getConnectCode(code: $cc) {
        user {
          ...userProfilePage
          __typename
        }
        __typename
      }
    }
    
    fragment userProfilePage on User {
      fbUid
      displayName
      connectCode {
        code
        __typename
      }
      rankedNetplayProfile {
        id
        ratingOrdinal
        ratingUpdateCount
        wins
        losses
        dailyGlobalPlacement
        dailyRegionalPlacement
        continent
        characters {
          id
          character
          gameCount
          __typename
        }
        __typename
      }
      __typename
    }
  `;

  // Variables for the query
  const variables = {
    cc: cc,
    uid: uid,
  };

  // Make the GraphQL request
  const response = await fetch('https://gql-gateway-dot-slippi.uc.r.appspot.com/graphql', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      variables,
    }),
  });

  const data = await response.json();
  const user = data.data.getConnectCode.user;
  return user;
}

class Rank {
  constructor(lower_bound, upper_bound, rank_name) {
    this.lower_bound = lower_bound;
    this.upper_bound = upper_bound;
    this.rank_name = rank_name;
  }
}

class GrandMaster extends Rank {
  constructor() {
    super(2191.75, Infinity, 'Grandmaster');
  }
}

const grand_master = new GrandMaster();

const rank_list = [
  new Rank(0, 765.42, 'Bronze 1'),
  new Rank(765.43, 913.71, 'Bronze 2'),
  new Rank(913.72, 1054.86, 'Bronze 3'),
  new Rank(1054.87, 1188.87, 'Silver 1'),
  new Rank(1188.88, 1315.74, 'Silver 2'),
  new Rank(1315.75, 1435.47, 'Silver 3'),
  new Rank(1435.48, 1548.06, 'Gold 1'),
  new Rank(1548.07, 1653.51, 'Gold 2'),
  new Rank(1653.52, 1751.82, 'Gold 3'),
  new Rank(1751.83, 1842.99, 'Platinum 1'),
  new Rank(1843, 1927.02, 'Platinum 2'),
  new Rank(1927.03, 2003.91, 'Platinum 3'),
  new Rank(2003.92, 2073.66, 'Diamond 1'),
  new Rank(2073.67, 2136.27, 'Diamond 2'),
  new Rank(2136.28, 2191.74, 'Diamond 3'),
  new Rank(2191.75, 2274.99, 'Master 1'),
  new Rank(2275, 2350, 'Master 2'),
  new Rank(2350, Infinity, 'Master 3')
];

function getRank(elo, dailyGlobalPlacement) {
  console.log(`getRank: ${elo}, ${dailyGlobalPlacement}`);

  if (dailyGlobalPlacement !== undefined) {
    return grand_master.rank_name;
  }

  for (let i = 0; i < rank_list.length; i++) {
    const rank = rank_list[i];
    if (elo >= rank.lower_bound && elo < rank.upper_bound) {
      return rank.rank_name;
    }
  }

  // If score is greater than the upper bound of the last rank, return the highest rank
  return rank_list[rank_list.length - 1].rank_name;
}
