import re
from flask import Flask, request, Response
# We use streamlink to catch video stream from web page or direct link.
from streamlink import Streamlink

app = Flask(__name__)
# Set video chunk size
buff_size = 1 << 17


@app.route('/')
def main():
    '''Parse query string, set options and get stream.'''
    try:
        # Get arguments passed with query string
        args = request.args
        # Available options
        if 'help' in args:
            return Response(Streamlink.set_option.__doc__, content_type='text/plain')
        # url should be either first argument or set explicitly with 'url' key.
        if 'url' not in args:
            url = next(iter(args))
        else:
            url = args['url']

        # Split url to url itself (url[0]) and stream (url[1]) if present.
        url = url.split()
        session = Streamlink()
        plugin = session.resolve_url(url[0])
        # Use remain arguments to set other options.
        for key in args:
            if re.match('[0-9]+$', args[key]):
                value = int(args[key])
            else:
                value = args[key]
            # Set session options described by help
            session.set_option(key, value)
            # Set plugin options if require (usually username and password)
            plugin.set_option(key, value)
        # Catch stream with given url
        streams = session.streams(url[0])
        # pick the stream
        if len(url) > 1:
            stream = streams[url[1]]
        else:
            # If specific stream is not provided in args, output list of available streams.
            return Response('Available streams: ' + str(list(streams.keys())) + '\n', content_type='text/plain')

        # Stream generator
        def generate(fd):
            chunk = True
            # Iterate over stream
            with fd:
                while chunk:
                    chunk = fd.read(buff_size)
                    # Read chunk of stream
                    yield chunk

        # Streaming to client
        # Open file like object of stream
        fd = stream.open()
        return Response(generate(fd), content_type='video/mpeg')
    except Exception or OSError as exception:
        error = 'Exception {0}: {1}\n'.format(type(exception).__name__, exception)
        return Response(error, content_type='text/plain')


# call script from command line for testing
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
