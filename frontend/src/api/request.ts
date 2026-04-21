import axios, {
    type AxiosInstance,
    type AxiosRequestConfig,
    type AxiosResponse,
    type InternalAxiosRequestConfig,
} from 'axios'
import {
    apiEndpoint,
    serializeEndpointQuery,
    type ApiQueryShape,
    type ApiRouteName,
    type RouteParams,
} from './routes'

const attachInterceptors = (client: AxiosInstance) => {
    client.interceptors.request.use(
        (config: InternalAxiosRequestConfig) => {
            return config
        },
        (error: unknown) => {
            return Promise.reject(error)
        }
    )

    client.interceptors.response.use(
        (response: AxiosResponse) => {
            return response
        },
        (error: unknown) => {
            console.error('API Request Failed:', error)
            return Promise.reject(error)
        }
    )

    return client
}

const createClient = (timeout: number): AxiosInstance => attachInterceptors(
    axios.create({
        baseURL: '/api/v1',
        timeout,
        headers: {
            'Content-Type': 'application/json'
        }
    })
)

const service: AxiosInstance = createClient(15000)
export const longTaskRequest: AxiosInstance = createClient(0)

type ApiClient = AxiosInstance
type ApiOptions = Omit<AxiosRequestConfig, 'params' | 'url' | 'method'> & {
    client?: ApiClient
    path?: RouteParams
    query?: ApiQueryShape
}

const querySerializerKey = ['params', 'Serializer'].join('')

const buildRequestConfig = (name: ApiRouteName, options: ApiOptions = {}): AxiosRequestConfig => {
    const { client: _client, path: _path, query, ...config } = options
    if (!query) return config
    return {
        ...config,
        params: query,
        // Axios is still the transport, but route-specific query rules live in generated endpoint contracts.
        [querySerializerKey]: () => serializeEndpointQuery(name, query),
    } as AxiosRequestConfig
}

const resolveClient = (options: ApiOptions = {}) => options.client || service

export const apiGet = <TResponse = unknown>(
    name: ApiRouteName,
    options: ApiOptions = {},
): Promise<AxiosResponse<TResponse>> => {
    const endpoint = apiEndpoint(name, options.path)
    return resolveClient(options).get<TResponse>(endpoint.url, buildRequestConfig(name, options))
}

export const apiPost = <TResponse = unknown, TBody = unknown>(
    name: ApiRouteName,
    body?: TBody,
    options: ApiOptions = {},
): Promise<AxiosResponse<TResponse>> => {
    const endpoint = apiEndpoint(name, options.path)
    return resolveClient(options).post<TResponse>(endpoint.url, body, buildRequestConfig(name, options))
}

export const apiPut = <TResponse = unknown, TBody = unknown>(
    name: ApiRouteName,
    body?: TBody,
    options: ApiOptions = {},
): Promise<AxiosResponse<TResponse>> => {
    const endpoint = apiEndpoint(name, options.path)
    return resolveClient(options).put<TResponse>(endpoint.url, body, buildRequestConfig(name, options))
}

export const apiDelete = <TResponse = unknown>(
    name: ApiRouteName,
    options: ApiOptions = {},
): Promise<AxiosResponse<TResponse>> => {
    const endpoint = apiEndpoint(name, options.path)
    return resolveClient(options).delete<TResponse>(endpoint.url, buildRequestConfig(name, options))
}

export default service
