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
