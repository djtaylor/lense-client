from os import path, listdir
from git import Repo, Git

class ClientGitHub(object):
    """
    Helper class for retrieving a lense project repository.
    """
    def __init__(self, local, remote, branch):
        """
        :param  local: Local path to clone to
        :type   local: str
        :param remote: The GitHub repository URL
        :type  remote: str
        :param branch: The repository branch
        :type  branch: str
        """
        
        # Local / remote / branch
        self.local    = LENSE.mkdir(local)
        self.remote   = remote
        self.branch   = branch

        # Repo / Git objects
        self._repo    = None
        self._git     = None

        # Has the repo been updated / cloned
        self.updated  = False
        self.cloned   = False

    def _exists(self):
        """
        Check if the local repo exists (path exists and is not empty)
        """
        if not path.isdir(self.local):
            return False
        if not listdir(self.local):
            return False
        return True

    def _get_current_branch(self):
        """
        Get the checked out local branch.
        """
        return str(self._repo.active_branch)

    def _checkout(self, branch):
        """
        Checkout the request branch.
        """
        current_branch = self._get_current_branch()

        # Target branch is already checked out
        if current_branch == branch:
            return True

        # Checkout the branch   
        self._git.checkout(branch)
        return LENSE.FEEDBACK.success('Switched to branch: {0}'.format(branch))
    
    def _clone(self):
        """
        Clone a remote repository.
        """
        if not self._exists():
            Repo.clone_from(self.remote, self.local)
            LENSE.FEEDBACK.success('Cloned repository')
            LENSE.FEEDBACK.info('Remote: {0}'.format(self.remote))
            LENSE.FEEDBACK.info('Local: {0}'.format(self.local))

            # Store the Repo/Git objects
            self._git  = Git(self.local)
            self._repo = Repo(self.local)

            # Checkout the requested branch
            self._checkout(self.branch)
            self.cloned = True

        # Local repo already exists
        else:
            LENSE.FEEDBACK.info('Local repository found: {0}'.format(self.local))

    def _refresh(self):
        """
        Refresh the repository objects.
        """
        self._git  = Git(self.local)
        self._repo = Repo(self.local)

        # Fetch remotes
        self._repo.remotes.origin.fetch()
        LENSE.FEEDBACK.info('Fetched changes from remote')

    def _get_local_commit(self):
        """
        Get the latest commit tag from the local branch.
        """
        for o in self._repo.refs:
            if o.name == self.branch:
                return o.commit
            
    def _get_remote_commit(self):
        """
        Get the latest commit tag from the remote branch.
        """
        for o in self._repo.remotes.origin.refs:
            if o.remote_head == self.branch:
                return o.commit

    def _pull(self):
        """
        Pull changes from a remote repository.
        """
        
        # If the repo has just been cloned
        if self.cloned:
            LENSE.FEEDBACK.info('Newly cloned repo, skipped pull')
            return True
        
        # Refresh repo objects
        self._refresh()

        # Checkout the branch
        self._checkout(self.branch)

        # Remote / local commits
        remote_commit = self._get_remote_commit()
        local_commit  = self._get_local_commit()

        # Show the local/remote commit info
        LENSE.FEEDBACK.info('Local <{0}> is on commit: {1}'.format(self.local, local_commit))
        LENSE.FEEDBACK.info('Remote <{0}> is on commit: {1}'.format(self.remote, remote_commit))

        # If local is up to date
        if remote_commit == local_commit:
            return LENSE.FEEDBACK.info('Local matches remote, everything up to date'.format(local_commit, remote_commit))

        # Update the local branch
        origin = self._repo.remotes.origin
        origin.pull()

        # Refresh the branches
        self._refresh()

        # Updated success
        LENSE.FEEDBACK.success('Local branch updated -> {0}'.format(self._get_local_commit()))
        self.updated = True
        
    @classmethod
    def clone(cls, local, remote, branch):
        """
        Clone a remote repository.
        
        :param  local: Local path to clone to
        :type   local: str
        :param remote: The GitHub repository URL
        :type  remote: str
        :param branch: The repository branch
        :type  branch: str
        """
        github = cls(local, remote, branch)._clone()
        
    @classmethod
    def pull(cls, local, remote, branch):
        """
        Pull changes from a remote repository.
        
        :param  local: Local path to clone to
        :type   local: str
        :param remote: The GitHub repository URL
        :type  remote: str
        :param branch: The repository branch
        :type  branch: str
        """
        github = cls(local, remote, branch)._pull()